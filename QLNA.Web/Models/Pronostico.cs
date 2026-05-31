using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class Pronostico
{
    [JsonPropertyName("id")]
    public int id { get; set; }
    [JsonPropertyName("partido_id")]
    public int partido_id { get; set; }
    [JsonPropertyName("goles_local")]
    public int? goles_local { get; set; }
    [JsonPropertyName("goles_visitante")]
    public int? goles_visitante { get; set; }
}
