#nullable enable

using System;
using System.IO;
using System.Reflection;
using System.Threading;

namespace RatVA
{
	public class Plugin
	{
		public static string VA_DisplayName()
		{
			return "Fuel Rat VA - v1.0.1";
		}

		public static string VA_DisplayInfo()
		{
			return "Fuel Rat Voice Attack interface.";
		}

		public static Guid VA_Id()
		{
			return new Guid("{7800C34F-2B98-4587-AAC1-59FF1FC03A67}");
		}

		public static void VA_Init1(dynamic vaProxy)
		{
			_voiceAttack = vaProxy;

			_voiceAttack.TextVariableChanged += new Action<string, string, string, Guid?>(TextVariableChanged);

			Log("FuelRatVA Initialised.");

			string assemblyFolder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
			string httpRoot = assemblyFolder + "\\HttpRoot";

			CommsServer.Start(httpRoot);

			_mainThread = new Thread(MainThread);
			_mainThread.Start();
		}

		public static void VA_Invoke1(dynamic vaProxy)
		{
			_voiceAttack = vaProxy;
			try
			{
				string context = _voiceAttack.Context.ToLower();
				if (context == "hello")
				{
					Log("Hello!");
				}
			}
			catch (Exception e)
			{
				LogError(e.Message);
			}
		}

		public static void VA_StopCommand() { }

		public static void VA_Exit1(dynamic vaProxy)
		{
			_shouldExit = true;
		}

		public static void TextVariableChanged(string name, string from, string to, Guid? internalID)
		{
			// Sample from bindED
			//if (name == "bindED.layout#")
			//{
			//    LogInfo($"Keyboard layout changed to '{to}', reloading …");
			//    Layout = to;
			//    try
			//    {
			//        LoadBinds(Binds);
			//    }
			//    catch (Exception e)
			//    {
			//        LogError(e.Message);
			//    }
			//}
		}

		private static dynamic? _voiceAttack;
		private static bool _shouldExit = false;
		private static Thread? _mainThread = null;

		public static void LogError(string message)
		{
			_voiceAttack!.WriteToLog($"FuelRatVA Error: {message}", "red");
		}

		public static void LogWarn(string message)
		{
			_voiceAttack!.WriteToLog($"FuelRatVA Warning: {message}", "yellow");
		}

		public static void Log(string message)
		{
			_voiceAttack!.WriteToLog($"FuelRatVA: {message}", "blue");
		}

		private static void MainThread()
		{
			do
			{
				//
			}
			while (!_shouldExit);
		}
	}
}
