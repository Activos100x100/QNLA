using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class Pronostico
{
    [JsonPropertyName("id")]
    public int id { get; set; }
    [JsonPropertyName("partido_Id")]
    public int partido_id { get; set; }
    [JsonPropertyName("goles_Local")]
    public int? goles_local { get; set; }
    [JsonPropertyName("goles_Visitante")]
    public int? goles_visitante { get; set; }
    [JsonPropertyName("puntos_Obtenidos")]
    public int? puntos_obtenidos { get; set; }
}
