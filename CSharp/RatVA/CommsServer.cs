using System;
using System.Text;
using System.Net;
using System.Threading.Tasks;
using System.IO;
using Newtonsoft.Json;
using System.Collections.Generic;
using System.Threading;
using System.Linq;

namespace RatVA
{
	public static class CommsServer
	{
		private static HttpListener? s_listener;
		private const string s_url = "http://localhost:8000/";
		private static bool s_serverRunning = false;

		private static Mutex s_mutex = new Mutex();
		private static Dictionary<int, CaseData> s_cases = new Dictionary<int, CaseData>();

		public static void Start()
		{
			if (s_serverRunning)
			{
				return;
			}

			s_serverRunning = true;

			s_listener = new HttpListener();
			s_listener.Prefixes.Add(s_url);
			s_listener.Start();

			Console.WriteLine("Started server at {0}.", s_url);

			Task requestHandler = HandleRequests();
			requestHandler.GetAwaiter().GetResult();

			s_listener.Close();
		}

		public static void Stop()
		{
			s_serverRunning = false;
			s_listener?.Stop();
		}

		private static async Task HandleRequests()
		{
			if(s_listener == null)
			{
				throw new Exception();
			}

			while (s_serverRunning)
			{
				HttpListenerContext context = await s_listener.GetContextAsync();
				HttpListenerRequest request = context.Request;
				HttpListenerResponse response = context.Response;

				Console.WriteLine(request.Url.ToString());
				Console.WriteLine(request.HttpMethod);
				Console.WriteLine(request.UserHostName);
				Console.WriteLine(request.UserAgent);
				Console.WriteLine();

				switch (request.HttpMethod)
				{
					case "POST":
						await HandlePost(request, response);
						break;
					case "GET":
						await HandleGet(request, response);
						break;
					case "DELETE":
						await HandleDelete(request, response);
						break;
				}

				response.Close();
			}
		}

		private static async Task HandlePost(HttpListenerRequest request, HttpListenerResponse response)
		{
			switch (request.Url.AbsolutePath)
			{
				case "/shutdown":
					await HandlePostShutdown(response);
					break;
				case "/case":
					await HandlePostCase(request, response);
					break;
				default:
					await SendError(response, 404, "Endpoint not found!");
					break;
			}
		}

		private static async Task HandleGet(HttpListenerRequest request, HttpListenerResponse response)
		{
			switch (request.Url.AbsolutePath)
			{
				case "/":
					await SendReport(response);
					break;
				default:
					await SendError(response, 404, "Endpoint not found!");
					break;
			}
		}

		private static async Task HandleDelete(HttpListenerRequest request, HttpListenerResponse response)
		{
			switch (request.Url.AbsolutePath)
			{
				case "/case":
					await HandleDeleteCase(request, response);
					break;
				default:
					await SendError(response, 404, "Endpoint not found!");
					break;
			}
		}

		private static async Task HandlePostShutdown(HttpListenerResponse response)
		{
			Console.WriteLine("Shutdown requested");
			s_serverRunning = false;

			await SendReport(response);
		}

		private static async Task HandlePostCase(HttpListenerRequest request, HttpListenerResponse response)
		{
			string json = ReadTextContent(request);
			Console.WriteLine(json);
			CaseData? caseData = JsonConvert.DeserializeObject<CaseData>(json);

			if(caseData == null)
			{
				return;
			}

			s_mutex.WaitOne();
			s_cases[caseData.Case] = caseData;
			s_mutex.ReleaseMutex();

			await SendText(response, "text/json", "{\"status\": \"accepted\"}");
		}

		private static async Task HandleDeleteCase(HttpListenerRequest request, HttpListenerResponse response)
		{
			await Task.FromException(new NotImplementedException());
		}

		private static async Task SendError(HttpListenerResponse response, int statusCode, string message)
		{
			response.StatusCode = statusCode;
			await SendText(response, "text/plain", message);
		}

		private static async Task SendReport(HttpListenerResponse response)
		{
			string disableSubmit = !s_serverRunning ? "disabled" : "";

			var properties = from property in typeof(CaseData).GetProperties()
							 where property.CanRead
							 select property;

			StringBuilder stringBuilder = new StringBuilder();
			stringBuilder.Append("<tr>");
			foreach (var property in properties)
			{
				stringBuilder.Append($"<th>{property.Name}</th>");
			}
			stringBuilder.Append("</tr>");
			string headerRow = stringBuilder.ToString();
			stringBuilder.Clear();

			foreach(KeyValuePair<int, CaseData> entry in s_cases.OrderBy(kvp => kvp.Value.Case))
			{
				CaseData caseData = entry.Value;
				stringBuilder.Append("<tr>");
				foreach (var property in properties)
				{
					var value = property.GetValue(caseData);
					string valString = value == null ? "None" : value.ToString();
					stringBuilder.Append($"<td>{valString}</td>");
				}
				stringBuilder.Append("</tr>");
			}
			string tableRows = stringBuilder.ToString();
			stringBuilder.Clear();

			const string pageData =
			"<!DOCTYPE>" +
			"<html>" +
				"<head>" +
					"<title>Fuel Rat Voice Attack Server</title>" +
				"</head>" +
				"<body>" +
					"<table>" +
						"{0}" +
						"{1}" +
					"</table>" +
				"</body>" +
			"</html>";

			string content = string.Format(pageData, headerRow, tableRows);

			await SendHtml(response, content);
		}

		private static async Task SendHtml(HttpListenerResponse response, string content)
		{
			await SendText(response, "text/html", content);
		}

		private static async Task SendText(HttpListenerResponse response, string mimeType, string content)
		{
			byte[] data = Encoding.UTF8.GetBytes(content);

			response.ContentType = mimeType;
			response.ContentEncoding = Encoding.UTF8;
			response.ContentLength64 = data.LongLength;

			await response.OutputStream.WriteAsync(data, 0, data.Length);
		}

		private static string ReadTextContent(HttpListenerRequest request)
		{
			using (var reader = new StreamReader(request.InputStream, Encoding.UTF8))
			{
				return reader.ReadToEnd();
			}
		}
	}
}