using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Windows.Forms;

namespace GokSetupWrapper;

internal static class Program
{
    private const string LogPathEnv = "GOK_SETUP_LOG_PATH";
    private const string CoreExeEnv = "GOK_SETUP_CORE_EXE";
    private const string CoreResourceName = "SetupCore.exe";

    [STAThread]
    private static int Main(string[] args)
    {
        string baseDir = AppContext.BaseDirectory;
        string logPath = ResolveLogPath();
        string? coreExe = ResolveCoreExe(baseDir, logPath);

        Log(logPath, $"Setup wrapper starting. BaseDir={baseDir}");
        Log(logPath, $"Args={string.Join(" ", args)}");

        if (string.IsNullOrWhiteSpace(coreExe) || !File.Exists(coreExe))
        {
            Log(logPath, $"Setup core missing. Expected={coreExe}");
            ShowError($"Installer core not found.\n\n{coreExe}");
            return 1;
        }

        try
        {
            var argList = BuildArguments(args, logPath);
            Log(logPath, $"Launching core installer: {coreExe}");

            var startInfo = new ProcessStartInfo(coreExe)
            {
                UseShellExecute = false
            };
            foreach (var arg in argList)
            {
                startInfo.ArgumentList.Add(arg);
            }

            using var process = Process.Start(startInfo);
            if (process == null)
            {
                Log(logPath, "Failed to start installer process.");
                ShowError("Failed to start installer.");
                return 1;
            }

            process.WaitForExit();
            Log(logPath, $"Installer exited with code {process.ExitCode}");
            return process.ExitCode;
        }
        catch (Exception ex)
        {
            Log(logPath, $"Installer failed: {ex}");
            ShowError($"Installer failed.\n\n{ex.Message}");
            return 1;
        }
    }

    private static string ResolveLogPath()
    {
        var env = Environment.GetEnvironmentVariable(LogPathEnv);
        if (!string.IsNullOrWhiteSpace(env))
        {
            return env;
        }

        var temp = Path.GetTempPath();
        return Path.Combine(temp, "GOK-setup.log");
    }

    private static string? ResolveCoreExe(string baseDir, string logPath)
    {
        var overridePath = Environment.GetEnvironmentVariable(CoreExeEnv);
        if (!string.IsNullOrWhiteSpace(overridePath))
        {
            return overridePath;
        }

        try
        {
            return ExtractEmbeddedSetupCore(logPath);
        }
        catch (Exception ex)
        {
            Log(logPath, $"Failed to extract embedded setup core: {ex}");
            return null;
        }
    }

    private static List<string> BuildArguments(string[] args, string logPath)
    {
        var argsList = new List<string>(args);
        int dashIndex = argsList.IndexOf("--");
        List<string> pre = dashIndex >= 0 ? argsList.Take(dashIndex).ToList() : new List<string>(argsList);
        List<string> post = dashIndex >= 0 ? argsList.Skip(dashIndex).ToList() : new List<string>();

        bool hasLog = pre.Any(arg => string.Equals(arg, "--log", StringComparison.OrdinalIgnoreCase));
        bool hasVerbose = pre.Any(arg => string.Equals(arg, "--verbose", StringComparison.OrdinalIgnoreCase));

        if (!hasLog)
        {
            pre.Insert(0, logPath);
            pre.Insert(0, "--log");
        }
        if (!hasVerbose)
        {
            pre.Insert(0, "--verbose");
        }

        pre.AddRange(post);
        return pre;
    }

    private static void Log(string logPath, string message)
    {
        try
        {
            var logDir = Path.GetDirectoryName(logPath);
            if (!string.IsNullOrWhiteSpace(logDir))
            {
                Directory.CreateDirectory(logDir);
            }

            var line = $"[{DateTime.UtcNow:O}] {message}{Environment.NewLine}";
            File.AppendAllText(logPath, line);
        }
        catch
        {
            // Ignore logging failures.
        }
    }

    private static void ShowError(string message)
    {
        try
        {
            MessageBox.Show(message, "Gardens of Karaxas Installer", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        catch
        {
            // Ignore UI failures.
        }
    }

    private static string ExtractEmbeddedSetupCore(string logPath)
    {
        var assembly = Assembly.GetExecutingAssembly();
        using var stream = assembly.GetManifestResourceStream(CoreResourceName);
        if (stream == null)
        {
            throw new InvalidOperationException("Embedded SetupCore.exe resource missing.");
        }

        var tempDir = Path.Combine(Path.GetTempPath(), "GardensOfKaraxas");
        Directory.CreateDirectory(tempDir);
        var tempPath = Path.Combine(tempDir, "GardensOfKaraxas-SetupCore.exe");

        using (var output = File.Create(tempPath))
        {
            stream.CopyTo(output);
        }

        Log(logPath, $"Extracted setup core to {tempPath}");
        return tempPath;
    }
}
