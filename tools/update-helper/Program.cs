using System;
using System.IO;
using System.Diagnostics;
using System.Threading.Tasks;
using Velopack;
using Velopack.Locators;
using Velopack.Sources;

internal static class Program
{
    private const int ExitNoUpdate = 2;

    public static async Task<int> Main(string[] args)
    {
        string? logFile = null;
        try
        {
            var options = ParseArgs(args);
            logFile = options.LogFile;
            Log(logFile, "Update helper starting.");
            var repoUrl = ResolveRepoUrl(options);
            if (string.IsNullOrWhiteSpace(repoUrl))
            {
                Log(logFile, "ERROR: Missing repo URL.");
                Console.WriteLine("ERROR: Missing repo URL.");
                return 1;
            }

            var token = ResolveToken(options);
            var prerelease = options.Prerelease;

            Log(logFile, $"Repo={repoUrl}");
            Log(logFile, $"Prerelease={prerelease}");
            Log(logFile, $"TokenPresent={!string.IsNullOrWhiteSpace(token)}");

            var source = new GithubSource(repoUrl, token, prerelease, null);
            var locator = VelopackLocator.CreateDefaultForPlatform(null);
            var mgr = new UpdateManager(source, options: null, locator: locator);

            Emit(logFile, "STATUS:CHECKING");
            var updateInfo = await mgr.CheckForUpdatesAsync();
            if (updateInfo == null)
            {
                Emit(logFile, "NO_UPDATE");
                return ExitNoUpdate;
            }

            Emit(logFile, "STATUS:DOWNLOADING");
            var lastProgress = -1;
            var totalBytes = EstimateTotalDownloadBytes(updateInfo);
            var stopwatch = Stopwatch.StartNew();
            await mgr.DownloadUpdatesAsync(updateInfo, progress =>
            {
                var numeric = Convert.ToDouble(progress);
                var clamped = Math.Clamp((int)Math.Round(numeric), 0, 100);
                if (clamped == lastProgress) return;
                lastProgress = clamped;
                if (totalBytes <= 0 || stopwatch.Elapsed.TotalSeconds <= 0.1) {
                    Emit(logFile, $"PROGRESS:{clamped}");
                    return;
                }
                var downloadedBytes = (long)Math.Round(totalBytes * (clamped / 100.0));
                var speedBytesPerSecond = downloadedBytes / stopwatch.Elapsed.TotalSeconds;
                Emit(logFile, $"PROGRESS:{clamped}:{(long)Math.Round(speedBytesPerSecond)}");
            });
            Emit(logFile, "UPDATE_DOWNLOADED");

            if (options.WaitPid > 0)
            {
                var waitPid = options.WaitPid;
                var restartArgs = options.RestartArgs ?? Array.Empty<string>();
                Emit(logFile, "STATUS:APPLYING");
                UpdateExe.Apply(locator, updateInfo.TargetFullRelease, silent: false, waitPid: (uint)waitPid, restart: true, restartArgs: restartArgs);
                Emit(logFile, "UPDATE_APPLYING");
                return 0;
            }

            Emit(logFile, "UPDATE_READY");
            return 0;
        }
        catch (Exception ex)
        {
            Log(logFile, $"ERROR: {ex}");
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

    private static string ResolveToken(Options options)
    {
        if (!string.IsNullOrWhiteSpace(options.Token)) return options.Token;
        if (!string.IsNullOrWhiteSpace(options.TokenFile) && File.Exists(options.TokenFile))
        {
            var content = File.ReadAllText(options.TokenFile).Trim();
            if (!string.IsNullOrWhiteSpace(content)) return content;
        }
        var env = Environment.GetEnvironmentVariable("VELOPACK_TOKEN")
                  ?? Environment.GetEnvironmentVariable("VELOPACK_GITHUB_TOKEN");
        return env ?? string.Empty;
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
                case "--token":
                    options.Token = NextValue(args, ref i);
                    break;
                case "--token-file":
                    options.TokenFile = NextValue(args, ref i);
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
        public string Token { get; set; } = string.Empty;
        public string TokenFile { get; set; } = string.Empty;
        public long WaitPid { get; set; }
        public bool Prerelease { get; set; }
        public string[]? RestartArgs { get; set; }
        public string? LogFile { get; set; }
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
}
