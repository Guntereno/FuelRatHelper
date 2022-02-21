﻿using Newtonsoft.Json;
using System;
using System.Text;
using System.Net;
using System.Threading.Tasks;
using System.IO;
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
			if (s_listener == null)
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
			string requestPath = request.Url.AbsolutePath;
			if (requestPath == "/")
			{
				requestPath = "/index.htm";
			}
			
			string httpRoot = Path.GetFullPath(".\\HttpRoot");
			string resourcePath = httpRoot + requestPath;

			if(!resourcePath.IsSubDirectoryOf(httpRoot))
			{
				throw new Exception("Requested asset is outside of http root!");
			}

			if (File.Exists(resourcePath))
			{
				await SendFile(response, resourcePath);
				return;
			}

			switch (requestPath)
			{
				case "/cases":
					await SendCases(response);
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

		private static async Task HandlePostCase(HttpListenerRequest request, HttpListenerResponse response)
		{
			string json = ReadTextContent(request);
			Console.WriteLine(json);
			CaseData? caseData = JsonConvert.DeserializeObject<CaseData>(json);

			if (caseData == null)
			{
				return;
			}

			s_mutex.WaitOne();
			s_cases[caseData.Case] = caseData;
			s_mutex.ReleaseMutex();

			await SendJson(response, "{\"status\": \"accepted\"}");
		}

		private static async Task HandleDeleteCase(HttpListenerRequest request, HttpListenerResponse response)
		{
			await Task.FromException(new NotImplementedException());
		}

		private static async Task SendError(HttpListenerResponse response, int statusCode, string message)
		{
			response.StatusCode = statusCode;
			await SendPlainText(response, message);
		}

		private static async Task SendCases(HttpListenerResponse response)
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

			foreach (KeyValuePair<int, CaseData> entry in s_cases.OrderBy(kvp => kvp.Value.Case))
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

			await SendHtml(response, stringBuilder.ToString());
		}

		private static async Task SendHtml(HttpListenerResponse response, string content)
		{
			await SendText(response, "text/html", content);
		}

		private static async Task SendJson(HttpListenerResponse response, string content)
		{
			await SendText(response, "text/json", content);
		}

		private static async Task SendPlainText(HttpListenerResponse response, string content)
		{
			await SendText(response, "text/plain", content);
		}

		private static async Task SendText(HttpListenerResponse response, string mimeType, string content)
		{
			byte[] contentBytes = Encoding.UTF8.GetBytes(content);
			await SendData(response, mimeType, contentBytes);
		}

		private static async Task SendFile(HttpListenerResponse response, string filePath)
		{
			FileStream fileStream = new FileStream(filePath, FileMode.Open, FileAccess.Read);
			byte[] data = new byte[fileStream.Length];
			fileStream.Read(data, 0, Convert.ToInt32(fileStream.Length));
			fileStream.Close();

			string? mimeType = GetMimeType(filePath);
			if (mimeType == null)
			{
				throw new Exception($"Couldn't establish MIME type for file '{filePath}'!");
			}

			await SendData(response, mimeType, data);
		}

		private static string? GetMimeType(string filePath)
		{
			FileInfo fileInfo = new FileInfo(filePath);
			switch (fileInfo.Extension)
			{
				case ".htm":
				case ".html":
					return "text/html";
				case ".css":
					return "text/css";
				default:
					return null;
			}
		}

		private static async Task SendData(HttpListenerResponse response, string mimeType, byte[] data)
		{
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