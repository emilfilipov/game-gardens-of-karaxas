using System;
using System.IO;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Text.Json;
using Velopack;
using Velopack.Locators;

internal static class Program
{
    private const int ExitNoUpdate = 2;
    private static readonly object StatusWriteLock = new();
    private static string? statusFilePath;

    public static async Task<int> Main(string[] args)
    {
        string? logFile = null;
        try
        {
            var options = ParseArgs(args);
            logFile = options.LogFile;
            statusFilePath = string.IsNullOrWhiteSpace(options.StatusFile) ? null : options.StatusFile;
            Log(logFile, "Update helper starting.");
            WriteStatus("launching", 0, 0, 0, 0, "Starting update helper.");
            var repoUrl = ResolveRepoUrl(options);
            if (string.IsNullOrWhiteSpace(repoUrl))
            {
                Log(logFile, "ERROR: Missing repo URL.");
                WriteStatus("error", 0, 0, 0, 0, "Missing update repository URL.");
                Console.WriteLine("ERROR: Missing repo URL.");
                return 1;
            }

            var prerelease = options.Prerelease;

            Log(logFile, $"Repo={repoUrl}");
            Log(logFile, $"Prerelease={prerelease}");

            var locator = VelopackLocator.CreateDefaultForPlatform(null);
            var mgr = new UpdateManager(repoUrl, options: null, locator: locator);

            Emit(logFile, "STATUS:CHECKING");
            WriteStatus("checking", 0, 0, 0, 0, "Checking for updates.");
            var updateInfo = await mgr.CheckForUpdatesAsync();
            if (updateInfo == null)
            {
                WriteStatus("no_update", 100, 0, 0, 0, "No updates available.");
                Emit(logFile, "NO_UPDATE");
                return ExitNoUpdate;
            }

            var (downloadMode, totalBytes) = EmitDownloadMode(logFile, updateInfo);
            Emit(logFile, "STATUS:DOWNLOADING");
            var lastProgress = -1;
            var stopwatch = Stopwatch.StartNew();
            await mgr.DownloadUpdatesAsync(updateInfo, progress =>
            {
                var numeric = Convert.ToDouble(progress);
                var clamped = Math.Clamp((int)Math.Round(numeric), 0, 100);
                if (clamped == lastProgress) return;
                lastProgress = clamped;
                var downloadedBytes = totalBytes > 0 ? (long)Math.Round(totalBytes * (clamped / 100.0)) : 0;
                var speedBytesPerSecond = stopwatch.Elapsed.TotalSeconds > 0.1
                    ? (long)Math.Round(downloadedBytes / stopwatch.Elapsed.TotalSeconds)
                    : 0;
                WriteStatus(
                    "downloading",
                    clamped,
                    speedBytesPerSecond,
                    downloadedBytes,
                    totalBytes,
                    $"Downloading update ({downloadMode})."
                );
                if (totalBytes <= 0 || stopwatch.Elapsed.TotalSeconds <= 0.1) {
                    Emit(logFile, $"PROGRESS:{clamped}");
                    return;
                }
                Emit(logFile, $"PROGRESS:{clamped}:{speedBytesPerSecond}");
            });
            WriteStatus("downloaded", 100, 0, totalBytes, totalBytes, "Download complete.");
            Emit(logFile, "UPDATE_DOWNLOADED");

            if (options.WaitPid > 0)
            {
                var waitPid = options.WaitPid;
                var restartArgs = options.RestartArgs ?? Array.Empty<string>();
                Emit(logFile, "STATUS:APPLYING");
                WriteStatus("applying", 100, 0, totalBytes, totalBytes, "Applying update and restarting.");
                UpdateExe.Apply(locator, updateInfo.TargetFullRelease, silent: true, waitPid: (uint)waitPid, restart: true, restartArgs: restartArgs);
                Emit(logFile, "UPDATE_APPLYING");
                return 0;
            }

            WriteStatus("ready", 100, 0, totalBytes, totalBytes, "Update downloaded and ready.");
            Emit(logFile, "UPDATE_READY");
            return 0;
        }
        catch (Exception ex)
        {
            Log(logFile, $"ERROR: {ex}");
            WriteStatus("error", 0, 0, 0, 0, ex.Message);
            Console.WriteLine($"ERROR: {ex.Message}");
            return 1;
        }
    }

    private static void Emit(string? logFile, string message)
    {
        Log(logFile, message);
        Console.WriteLine(message);
    }

    private static string ResolveRepoUrl(Options options)
    {
        if (!string.IsNullOrWhiteSpace(options.RepoUrl)) return options.RepoUrl;
        if (!string.IsNullOrWhiteSpace(options.RepoFile) && File.Exists(options.RepoFile))
        {
            var content = File.ReadAllText(options.RepoFile).Trim();
            if (!string.IsNullOrWhiteSpace(content)) return content;
        }
        var env = Environment.GetEnvironmentVariable("GOK_UPDATE_REPO")
                  ?? Environment.GetEnvironmentVariable("VELOPACK_UPDATE_REPO")
                  ?? Environment.GetEnvironmentVariable("UPDATE_REPO_URL");
        return env ?? string.Empty;
    }

    private static long EstimateTotalDownloadBytes(UpdateInfo info)
    {
        long total = 0;
        if (info.DeltasToTarget != null && info.DeltasToTarget.Length > 0)
        {
            foreach (var delta in info.DeltasToTarget)
            {
                if (delta != null && delta.Size > 0) total += delta.Size;
            }
            if (total > 0) return total;
        }
        var full = info.TargetFullRelease;
        if (full != null && full.Size > 0) {
            return full.Size;
        }
        return 0;
    }

    private static (string mode, long totalBytes) EmitDownloadMode(string? logFile, UpdateInfo info)
    {
        if (info.DeltasToTarget != null && info.DeltasToTarget.Length > 0)
        {
            long size = 0;
            foreach (var delta in info.DeltasToTarget)
            {
                if (delta != null && delta.Size > 0) size += delta.Size;
            }
            Emit(logFile, $"DOWNLOAD_MODE:DELTA:{info.DeltasToTarget.Length}:{size}");
            return ("delta", size);
        }

        var fullSize = info.TargetFullRelease?.Size ?? 0;
        Emit(logFile, $"DOWNLOAD_MODE:FULL:{fullSize}");
        return ("full", fullSize);
    }

    private static Options ParseArgs(string[] args)
    {
        var options = new Options();
        for (var i = 0; i < args.Length; i++)
        {
            var arg = args[i];
            switch (arg)
            {
                case "--repo":
                    options.RepoUrl = NextValue(args, ref i);
                    break;
                case "--repo-file":
                    options.RepoFile = NextValue(args, ref i);
                    break;
                case "--waitpid":
                    if (long.TryParse(NextValue(args, ref i), out var pid)) options.WaitPid = pid;
                    break;
                case "--prerelease":
                    options.Prerelease = true;
                    break;
                case "--restart-args":
                    options.RestartArgs = NextValue(args, ref i).Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    break;
                case "--log-file":
                    options.LogFile = NextValue(args, ref i);
                    break;
                case "--status-file":
                    options.StatusFile = NextValue(args, ref i);
                    break;
            }
        }
        return options;
    }

    private static string NextValue(string[] args, ref int index)
    {
        if (index + 1 >= args.Length) return string.Empty;
        index++;
        return args[index];
    }

    private sealed class Options
    {
        public string RepoUrl { get; set; } = string.Empty;
        public string RepoFile { get; set; } = string.Empty;
        public long WaitPid { get; set; }
        public bool Prerelease { get; set; }
        public string[]? RestartArgs { get; set; }
        public string? LogFile { get; set; }
        public string? StatusFile { get; set; }
    }

    private static void Log(string? logFile, string message)
    {
        if (string.IsNullOrWhiteSpace(logFile)) return;
        try
        {
            var line = $"[{DateTime.UtcNow:O}] {message}{Environment.NewLine}";
            File.AppendAllText(logFile, line);
        }
        catch
        {
            // Ignore logging failures.
        }
    }

    private static void WriteStatus(
        string status,
        int percent,
        long speedBytesPerSecond,
        long downloadedBytes,
        long totalBytes,
        string message
    )
    {
        if (string.IsNullOrWhiteSpace(statusFilePath)) return;
        try
        {
            var path = statusFilePath!;
            var directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrWhiteSpace(directory))
            {
                Directory.CreateDirectory(directory);
            }
            var payload = new
            {
                status = status,
                percent = Math.Clamp(percent, 0, 100),
                speed_bps = Math.Max(0, speedBytesPerSecond),
                downloaded_bytes = Math.Max(0, downloadedBytes),
                total_bytes = Math.Max(0, totalBytes),
                message = message,
                updated_at = DateTime.UtcNow.ToString("O"),
            };
            var json = JsonSerializer.Serialize(payload);
            lock (StatusWriteLock)
            {
                File.WriteAllText(path, json);
            }
        }
        catch
        {
            // Ignore status write failures.
        }
    }
}
