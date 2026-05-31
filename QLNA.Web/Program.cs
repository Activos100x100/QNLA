using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Mvc;
using QLNA.Web.Components;
using QLNA.Web.Models;
using QLNA.Web.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

builder.Services.AddCascadingAuthenticationState();
builder.Services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.LoginPath = "/login";
        options.AccessDeniedPath = "/login";
        options.ExpireTimeSpan = TimeSpan.FromDays(7);
        options.SlidingExpiration = true;
        options.Cookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
    });
builder.Services.AddAuthorization();
builder.Services.AddHttpContextAccessor();
builder.Services.AddAntiforgery();

builder.Services.AddScoped<SessionTokenStore>();
builder.Services.AddScoped<AuthStateProvider>();

builder.Services.AddHttpClient<ApiService>((sp, client) =>
{
    var config = sp.GetRequiredService<IConfiguration>();
    var baseUrl = config["Api:BaseUrl"] ?? "https://qnla-api-659774952506.europe-west1.run.app";
    client.BaseAddress = new Uri(baseUrl);
    client.Timeout = TimeSpan.FromSeconds(30);
});

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/error", createScopeForErrors: true);
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();
app.UseAntiforgery();

app.MapPost("/auth/login", async (
    [FromForm] LoginForm form,
    HttpContext httpContext,
    ApiService apiService) =>
{
    if (string.IsNullOrWhiteSpace(form.DniNie) || string.IsNullOrWhiteSpace(form.Password))
    {
        return Results.LocalRedirect("/login?error=missing");
    }

    var ok = await apiService.LoginAsync(form.DniNie.Trim(), form.Password);
    var user = apiService.UsuarioActual;
    if (!ok || user is null)
    {
        return Results.LocalRedirect("/login?error=invalid");
    }

    var claims = new List<Claim>
    {
        new(ClaimTypes.NameIdentifier, ResolveUserId(user)),
        new(ClaimTypes.Name, user.nombre ?? user.usuario?.nombre ?? form.DniNie.Trim()),
        new("access_token", user.access_token ?? string.Empty)
    };
    var identity = new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme);

    await httpContext.SignInAsync(
        CookieAuthenticationDefaults.AuthenticationScheme,
        new ClaimsPrincipal(identity),
        new AuthenticationProperties { IsPersistent = true });

    return Results.LocalRedirect("/pronosticos");
}).AllowAnonymous();

app.MapPost("/auth/logout", async (HttpContext httpContext) =>
{
    await httpContext.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
    return Results.LocalRedirect("/login");
}).AllowAnonymous();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();

static string ResolveUserId(LoginResponse user)
    => user.usuario_id?.ToString()
        ?? user.usuario?.usuario_id?.ToString()
        ?? user.usuario?.empleado_id?.ToString()
        ?? "0";

internal sealed class LoginForm
{
    public string DniNie { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}
