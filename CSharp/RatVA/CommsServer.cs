using Newtonsoft.Json;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using System.Threading;
using System;
using Newtonsoft.Json.Linq;
using System.Reflection;

namespace RatVA
{
	public static class CommsServer
	{
		private struct ResponseData
		{
			public int StatusCode;
			public string MimeType;
			public byte[] Data;

			public async Task Send(HttpListenerResponse response)
			{
				response.ContentType = MimeType;
				response.ContentEncoding = Encoding.UTF8;
				response.ContentLength64 = Data.LongLength;

				await response.OutputStream.WriteAsync(Data, 0, Data.Length);
			}
		}

		private static HttpListener? s_listener;
		private const string s_url = "http://localhost:8000/";
		private static bool s_serverRunning = false;

		private static Mutex s_mutex = new Mutex();
		private static Dictionary<int, CaseData> s_cases = new Dictionary<int, CaseData>();

		private static string s_httpRoot = "";

		public static void Start(string httpRoot)
		{
			s_httpRoot = httpRoot;

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

				ResponseData responseData;
				switch (request.HttpMethod)
				{
					case "POST":
						{
							responseData = HandlePost(request);
							break;
						}

					case "GET":
						{
							responseData = HandleGet(request);
							break;
						}

					case "DELETE":
						{
							responseData = HandleDelete(request);
							break;
						}

					case "PATCH":
						{
							responseData = HandlePatch(request);
							break;
						}

					default:
						{
							responseData = CreateErrorResponseData(404, "Endpoint not found!");
							break;
						}
				}

				await responseData.Send(response);

				response.Close();
			}
		}

		private static ResponseData HandlePost(HttpListenerRequest request)
		{
			switch (request.Url.AbsolutePath)
			{
				case "/case":
					{
						return HandlePostCase(request);
					}

				case "/note":
					{
						return HandlePostNote(request);
					}

				default:
					{
						return CreateErrorResponseData(404, "Endpoint not found!");
					}
			}
		}

		private static ResponseData HandleGet(HttpListenerRequest request)
		{
			try
			{
				string requestPath = request.Url.AbsolutePath;

				switch (requestPath)
				{
					case "/cases":
						{
							return BuildCasesResponse();
						}

					default:
						// Continue
						break;
				}

				if (requestPath == "/")
				{
					requestPath = "/index.htm";
				}

				string httpRoot = Path.GetFullPath(s_httpRoot);
				string resourcePath = httpRoot + requestPath;

				if (!resourcePath.IsSubDirectoryOf(httpRoot))
				{
					return CreateErrorResponseData(404, "Endpoint not found!");
				}

				if (!File.Exists(resourcePath))
				{
					throw new FileNotFoundException(resourcePath);
				}

				return CreateFileResponseData(resourcePath);
			}
			catch (Exception e)
			{
				return CreateErrorResponseData(404, $"{e}");
			}
		}

		private static ResponseData HandleDelete(HttpListenerRequest request)
		{
			switch (request.Url.AbsolutePath)
			{
				case "/case":
					{
						return HandleDeleteCase(request);
					}
				case "/note":
					{
						return HandleDeleteNote(request);
					}
				default:
					{
						return CreateErrorResponseData(404, "Endpoint not found!");
					}
			}
		}

		private static ResponseData HandlePatch(HttpListenerRequest request)
		{
			switch (request.Url.AbsolutePath)
			{
				case "/case":
					{
						return HandlePatchCase(request);
					}
				case "/note":
					{
						return HandlePatchNote(request);
					}
				default:
					{
						return CreateErrorResponseData(404, "Endpoint not found!");
					}
			}
		}

		private static ResponseData HandlePostCase(HttpListenerRequest request)
		{
			string json = ReadTextContent(request);
			Console.WriteLine(json);
			CaseData? caseData = JsonConvert.DeserializeObject<CaseData>(json);

			if (caseData == null)
			{
				return CreateErrorResponseData(400, "Invalid request!");
			}

			s_mutex.WaitOne();
			s_cases[caseData.Case] = caseData;
			s_mutex.ReleaseMutex();

			return CreateJsonResponseData("{\"status\": \"accepted\"}");
		}

		private static ResponseData HandleDeleteCase(HttpListenerRequest request)
		{
			bool foundResource = false;

			string json = ReadTextContent(request);
			Console.WriteLine(json);

			JObject jObject = JObject.Parse(json);
			if (jObject.TryGetValue("case", out JToken? value))
			{
				int caseId = (int)value;

				s_mutex.WaitOne();
				if (s_cases.ContainsKey(caseId))
				{
					s_cases.Remove(caseId);
					foundResource = true;
				}
				s_mutex.ReleaseMutex();
			}

			if (foundResource)
			{
				return CreateJsonResponseData("{\"status\": \"deleted\"}");
			}
			else
			{
				return CreateErrorResponseData(404, "Endpoint not found!");
			}
		}

		private static ResponseData HandlePostNote(HttpListenerRequest request)
		{
			return ModifyCase(request, (caseData, requestData) =>
			{
				string? note = GetRequestString(requestData, "note");
				if (note != null)
				{
					caseData.AddNote(note);
					return CreateJsonResponseData(JsonConvert.SerializeObject(caseData));
				}
				else
				{
					return CreateErrorResponseData(400, "No note specified!");
				}
			});
		}

		private static ResponseData HandlePatchNote(HttpListenerRequest request)
		{
			return ModifyCase(request, (caseData, requestData) =>
			{
				string? note = GetRequestString(requestData, "note");
				int? line = GetRequestInt(requestData, "line");

				if((note != null) && (line != null))
				{
					int lineIndex = GetLineIndex((int)line);
					if ((lineIndex >= 0) && (lineIndex < caseData.Notes?.Count))
					{
						caseData.Notes[lineIndex] = (string)note;
						return CreateJsonResponseData(JsonConvert.SerializeObject(caseData));
					}
					else
					{
						return CreateErrorResponseData(404, "Invalid note line!");
					}
				}
				else
				{
					return CreateErrorResponseData(400, "Invalid request!");
				}
			});
		}

		private static int GetLineIndex(int line)
		{
			// Line numbers reported by MechaSqueak are 1 indexed.
			return line - 1;
		}

		private static ResponseData HandleDeleteNote(HttpListenerRequest request)
		{
			return ModifyCase(request, (caseData, requestData) =>
			{
				int? line = GetRequestInt(requestData, "line");

				if (line != null)
				{
					int lineIndex = GetLineIndex((int)line);
					if ((lineIndex >= 0) && (lineIndex < caseData.Notes?.Count))
					{
						caseData.Notes.RemoveAt((int)lineIndex);
						return CreateJsonResponseData(JsonConvert.SerializeObject(caseData));
					}
					else
					{
						return CreateErrorResponseData(404, "Invalid note line!");
					}
				}
				else
				{
					return CreateErrorResponseData(400, "Invalid request!");
				}
			});
		}

		private static string? GetRequestString(JObject requestData, string key)
		{
			return (requestData.ContainsKey(key) && (requestData[key] != null)) ?
					requestData[key]?.ToString() :
					null;
		}

		private static int? GetRequestInt(JObject requestData, string key)
		{
			return (requestData.ContainsKey(key) && (requestData[key] != null)) ?
					requestData[key]?.ToObject<int>() :
					null;
		}

		private static ResponseData ModifyCase(
			HttpListenerRequest request,
			Func<CaseData, JObject, ResponseData> callBack)
		{
			string json = ReadTextContent(request);
			Console.WriteLine(json);

			JObject requestData = JObject.Parse(json);

			CaseData? referencedCase = null;
			ResponseData response;
			int? caseId = GetRequestInt(requestData, "case"); 

			if (caseId != null)
			{
				s_mutex.WaitOne();

				referencedCase = s_cases.ContainsKey((int)caseId) ? s_cases[(int)caseId] : null;

				if (referencedCase != null)
				{
					response = callBack(referencedCase, requestData);
				}
				else
				{
					response = CreateErrorResponseData(404, "Case not found!");
				}

				s_mutex.ReleaseMutex();
			}
			else
			{
				response = CreateErrorResponseData(400, "Case not spcified!");
			}

			return response;
		}

		private static ResponseData BuildCasesResponse()
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
				foreach (PropertyInfo? property in properties)
				{
					var value = property.GetValue(caseData);

					string valString;
					if (value == null)
					{
						valString = "None";
					}
					else if (value is IEnumerable<string>)
					{
						var listBuilder = new StringBuilder();
						listBuilder.Append("<ol>");
						var strIter = (IEnumerable<string>)value;
						foreach (string listItem in strIter)
						{
							listBuilder.Append($"<li>{listItem}</li>");
						}
						listBuilder.Append("</ol>");
						valString = listBuilder.ToString();
					}
					else
					{
						valString = value.ToString();
					}
					stringBuilder.Append($"<td>{valString}</td>");
				}
				stringBuilder.Append("</tr>");
			}

			return CreateHtmlResponseData(stringBuilder.ToString());
		}

		private static ResponseData HandlePatchCase(HttpListenerRequest request)
		{
			return ModifyCase(request, (caseData, requestData) =>
			{
				{
					if (requestData.ContainsKey("system"))
					{
						caseData.System = requestData["system"]?.ToString();
					}
				}

				{
					if (requestData.ContainsKey("desc"))
					{
						caseData.Desc = requestData["sydescstem"]?.ToString();
					}
				}

				{
					if (requestData.ContainsKey("client"))
					{
						caseData.Cmdr = requestData["client"]?.ToString();
					}
				}

				return CreateJsonResponseData(JsonConvert.SerializeObject(caseData));
			});
		}


		private static ResponseData CreateErrorResponseData(int statusCode, string message)
		{
			ResponseData data = CreatePlainTextResponseData(message);
			data.StatusCode = statusCode;
			return data;
		}

		private static ResponseData CreateHtmlResponseData(string content)
		{
			return CreateTextResponseData("text/html", content);
		}

		private static ResponseData CreateJsonResponseData(string content)
		{
			return CreateTextResponseData("text/json", content);
		}

		private static ResponseData CreatePlainTextResponseData(string content)
		{
			return CreateTextResponseData("text/plain", content);
		}

		private static ResponseData CreateTextResponseData(string mimeType, string content)
		{
			byte[] contentBytes = Encoding.UTF8.GetBytes(content);
			return CreateResponseData(mimeType, contentBytes);
		}

		private static ResponseData CreateFileResponseData(string filePath)
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

			return CreateResponseData(mimeType, data);
		}

		private static ResponseData CreateResponseData(string mimeType, byte[] data)
		{
			return new ResponseData
			{
				StatusCode = 200,
				MimeType = mimeType,
				Data = data
			};
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

		private static string ReadTextContent(HttpListenerRequest request)
		{
			using (var reader = new StreamReader(request.InputStream, Encoding.UTF8))
			{
				return reader.ReadToEnd();
			}
		}
	}
}