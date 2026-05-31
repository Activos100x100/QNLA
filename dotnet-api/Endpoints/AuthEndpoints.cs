using Microsoft.AspNetCore.Authorization;
using QNLA.Api.Auth;
using QNLA.Api.Models;
using QNLA.Api.Services;

namespace QNLA.Api.Endpoints;

public static class AuthEndpoints
{
    public static RouteGroupBuilder MapAuthEndpoints(this RouteGroupBuilder group)
    {
        group.MapPost("/login", async (LoginRequest request, IAuthService authService) =>
        {
            var result = await authService.LoginAsync(request);
            return result is null ? Results.Unauthorized() : Results.Ok(result);
        })
        .AllowAnonymous();

        group.MapPost("/refresh", async (RefreshRequest request, IAuthService authService) =>
        {
            var result = await authService.RefreshAsync(request.Refresh_Token);
            return result is null ? Results.Unauthorized() : Results.Ok(result);
        })
        .AllowAnonymous();

        group.MapGet("/me", [Authorize] async (ICurrentUser currentUser, IAuthService authService) =>
        {
            if (currentUser.EmpleadoId is null)
            {
                return Results.Unauthorized();
            }

            var user = await authService.GetCurrentUserAsync(currentUser.EmpleadoId.Value, currentUser.DniNie);
            return user is null ? Results.Unauthorized() : Results.Ok(user);
        });

        group.MapPut("/me/{torneoId:int}", async (int torneoId, UpdateParticipantRequest request, ICurrentUser currentUser, IParticipantService participantService) =>
        {
            if (currentUser.EmpleadoId is null)
            {
                return Results.Unauthorized();
            }

            var result = await participantService.UpdateMyParticipantAsync(
                torneoId,
                currentUser.EmpleadoId.Value,
                request);

            return result is null ? Results.NotFound() : Results.Ok(result);


        });

       return group;
    }
}
