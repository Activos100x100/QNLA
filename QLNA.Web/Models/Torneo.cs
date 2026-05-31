using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class Torneo
{
    [JsonPropertyName("id")]
    public int id { get; set; }
    [JsonPropertyName("nombre")]
    public string? nombre { get; set; }
    public string? descripcion { get; set; }
    [JsonPropertyName("activo")]
    public bool activo { get; set; }
}
