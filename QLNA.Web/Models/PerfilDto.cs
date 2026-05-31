using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class PerfilDto
{
    [JsonPropertyName("id")]
    public int usuario_id { get; set; }
    [JsonPropertyName("nombre")]
    public string? nombre { get; set; }
    [JsonPropertyName("alias")]
    public string? alias { get; set; }
    [JsonPropertyName("email")]
    public string? email { get; set; }
    public string? telefono { get; set; }
    public int puntos { get; set; }
    public int posicion { get; set; }
}
