using System.Text.Json.Serialization;

namespace QLNA.Web.Models;

public class ActualizarPerfilRequest
{
    [JsonPropertyName("nombre")]
    public string? nombre { get; set; }
    [JsonPropertyName("alias")]
    public string? alias { get; set; }
    [JsonPropertyName("email")]
    public string? email { get; set; }
    [JsonPropertyName("telefono")]
    public string? telefono { get; set; }
}
