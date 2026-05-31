using Microsoft.AspNetCore.Authorization;
using QNLA.Api.Auth;
using QNLA.Api.Models;
using QNLA.Api.Services;

namespace QNLA.Api.Endpoints;

public static class ParticipantsEndpoints
{
    public static RouteGroupBuilder MapParticipantsEndpoints(this RouteGroupBuilder group)
    {

        group.MapGet("perfil/{torneoId:int}", [Authorize] async (int torneoId, ICurrentUser currentUser, IParticipantService participantService) =>
        {
            if (currentUser.EmpleadoId is null)
            {
                return Results.Unauthorized();
            }

            var user = await participantService.GetMyParticipantAsync(torneoId, currentUser.EmpleadoId.Value);
            return user is null ? Results.Unauthorized() : Results.Ok(user);
        });

        group.MapPut("/perfil/{torneoId:int}", async (int torneoId, UpdateParticipantRequest request, ICurrentUser currentUser, IParticipantService participantService) =>
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