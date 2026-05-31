namespace QLNA.Web.Services;

public class SessionTokenStore
{
    private readonly IHttpContextAccessor _http;

    public SessionTokenStore(IHttpContextAccessor http)
    {
        _http = http;
    }

    public string? GetAccessToken()
        => _http.HttpContext?.User?.FindFirst("access_token")?.Value;
}
