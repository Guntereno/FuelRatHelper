
using Newtonsoft.Json;

namespace RatVA
{
	[JsonObject(MemberSerialization.OptIn)]
	public class CaseData
	{
		[JsonProperty(propertyName: "case")]
		public int Case { get; set; }

		[JsonProperty(propertyName: "platform")]
		public string? Platform { get; set; }

		[JsonProperty(propertyName: "code_red")]
		public bool CodeRed { get; set; }

		[JsonProperty(propertyName: "odyssey")]
		public bool Odyssey { get; set; }

		[JsonProperty(propertyName: "cmdr")]
		public string? Cmdr { get; set; }

		[JsonProperty(propertyName: "system")]
		public string? System { get; set; }

		[JsonProperty(propertyName: "desc")]
		public string? Desc { get; set; }

		[JsonProperty(propertyName: "permit")]
		public string? Permit { get; set; }

		[JsonProperty(propertyName: "language")]
		public string? Language { get; set; }

		[JsonProperty(propertyName: "locale")]
		public string? Locale { get; set; }

		[JsonProperty(propertyName: "nick")]
		public string? Nick { get; set; }

		[JsonProperty(propertyName: "signal")]
		public string? Signal { get; set; }
	}
}
