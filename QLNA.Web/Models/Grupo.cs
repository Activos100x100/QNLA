using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class Grupo
{
    [JsonPropertyName("id")]
    public int id { get; set; }
    [JsonPropertyName("torneoId")]
    public int torneo_id { get; set; }
    [JsonPropertyName("nombre")]
    public string? nombre { get; set; }
    [JsonPropertyName("partidos")]
    public List<Partido>? partidos { get; set; }
}
