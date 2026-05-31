using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using QNLA.Api.Auth;
using QNLA.Api.Data;
using QNLA.Api.Endpoints;
using QNLA.Api.Models;
using QNLA.Api.Services;

var builder = WebApplication.CreateBuilder(args);

var port = Environment.GetEnvironmentVariable("PORT") ?? "8081";
builder.WebHost.UseUrls($"http://0.0.0.0:{port}");

builder.Services.Configure<JwtOptions>(builder.Configuration.GetSection("Jwt"));
builder.Services.Configure<PasswordHashingOptions>(builder.Configuration.GetSection("Auth:PasswordHashing"));

var jwtOptions = builder.Configuration.GetSection("Jwt").Get<JwtOptions>() ?? new JwtOptions();
if (string.IsNullOrWhiteSpace(jwtOptions.Secret) || jwtOptions.Secret.Length < 32)
{
    throw new InvalidOperationException("Jwt:Secret must be configured with at least 32 characters.");
}

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateIssuerSigningKey = true,
            ValidateLifetime = true,
            ValidIssuer = jwtOptions.Issuer,
            ValidAudience = jwtOptions.Audience,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtOptions.Secret)),
            ClockSkew = TimeSpan.Zero,
            NameClaimType = System.Security.Claims.ClaimTypes.NameIdentifier
        };
    });

builder.Services.AddAuthorization();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "QNLA API", Version = "v1" });
    var scheme = new OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        In = ParameterLocation.Header,
        Description = "Use: Bearer {token}",
        Reference = new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" }
    };
    c.AddSecurityDefinition("Bearer", scheme);
    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            scheme,
            Array.Empty<string>()
        }
    });
});

builder.Services.AddCors(options =>
{
    options.AddPolicy("Open", policy =>
        policy.AllowAnyOrigin()
            .AllowAnyMethod()
            .AllowAnyHeader());
});

builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<ICurrentUser, CurrentUser>();
builder.Services.AddSingleton<IConnectionFactory, ConnectionFactory>();
builder.Services.AddSingleton<IJwtService, JwtService>();
builder.Services.AddSingleton<IPasswordHasher, PasswordHasher>();
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IPronosticoService, PronosticoService>();
builder.Services.AddScoped<IRankingService, RankingService>();
builder.Services.AddScoped<IParticipantService, ParticipantService>();

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();

app.UseCors("Open");
app.UseAuthentication();
app.UseAuthorization();

app.MapHealthEndpoints();

var v1 = app.MapGroup("/api/v1");
v1.MapGroup("/auth").MapAuthEndpoints();
v1.MapGroup("/pronosticos").MapPronosticosEndpoints();
v1.MapGroup("/torneos").MapTorneosEndpoints();
v1.MapGroup("/participante").MapParticipantsEndpoints();

app.Run();
