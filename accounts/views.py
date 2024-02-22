from django.http import JsonResponse
from django.shortcuts import redirect, render

from accounts.auth import DiscordAuthService, SteamAuthService
from accounts.schemas import SteamAuthSchema
from players.models import DiscordUser, Player, SteamUser

def redirect_to_discord(request):
    discord_auth = DiscordAuthService()
    return redirect(discord_auth.get_login_url())

def discord_callback(request):
    code = request.GET.get("code")

    discord_auth = DiscordAuthService()
    token = discord_auth.exchange_code(code)
    user = discord_auth.get_user_info(token["access_token"])
    request.session["dc_user"] = user
    dc_user = DiscordUser.objects.get_or_create(user_id=user["id"], username=user["username"])
    print(dc_user)
    return redirect("/accounts/steam/")


def redirect_to_steam(request):
    dc_user = request.session.get("dc_user", None)
    if not dc_user:
        return redirect("/accounts/discord/")
    steam_auth = SteamAuthService()
    return redirect(steam_auth.get_login_url())

def steam_callback(request):
    if request.GET.get("openid.mode") != "id_res":
        return JsonResponse({"error": "Invalid openid mode"}, status=400)
    if not request.session.get("dc_user"):
        return JsonResponse({"error": "Invalid discord user"}, status=400)
    params = SteamAuthSchema(
        openid_ns=request.GET.get("openid.ns"),
        openid_mode=request.GET.get("openid.mode"),
        openid_op_endpoint=request.GET.get("openid.op_endpoint"),
        openid_claimed_id=request.GET.get("openid.claimed_id"),
        openid_identity=request.GET.get("openid.identity"),
        openid_return_to=request.GET.get("openid.return_to"),
        openid_response_nonce=request.GET.get("openid.response_nonce"),
        openid_assoc_handle=request.GET.get("openid.assoc_handle"),
        openid_signed=request.GET.get("openid.signed"),
        openid_sig=request.GET.get("openid.sig"),
    )
    steam_service = SteamAuthService()
    steamid64 = steam_service.authenticate(request.session.get("user"), params)
    player_info = steam_service.get_player_info(steamid64)
    steam_user, created = SteamUser.objects.get_or_create(steamid64=player_info["steamid64"], username=player_info["username"], steamid32=player_info["steamid32"], profile_url=player_info["profile_url"], avatar=player_info["avatar"])
    discord_user_session = request.session.get("dc_user", None)
    discord_user = DiscordUser.objects.get(user_id=discord_user_session["id"])
    Player.objects.get_or_create(discord_user=discord_user, steam_user=steam_user)
    return redirect("/accounts/success/")


def success(request):

    return render(request, "accounts/success.html")