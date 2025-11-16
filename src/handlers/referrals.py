import logging
from aiohttp import web
import aiohttp_jinja2


class ReferralsHandlers:
    """Handlers for referral system management."""

    def __init__(self, panel_instance):
        self.panel = panel_instance
        self.logger = logging.getLogger(self.__class__.__name__)

    @aiohttp_jinja2.template('referrals.html')
    async def _handle_referrals(self, request):
        """Referral system page."""
        return {'active_page': 'referrals'}

    async def _api_get_user_referrals(self, request):
        """Get user's referral information (proxy to Bot API)."""
        user_id = request.match_info['user_id']
        self.logger.debug(f'Getting referrals for user: {user_id}')
        return web.json_response(
            await self.panel.api_request('GET', f'/api/referrals/{user_id}')
        )

    async def _api_get_referral_history(self, request):
        """Get user's points transaction history (proxy to Bot API)."""
        user_id = request.match_info['user_id']
        query_string = request.query_string
        endpoint = f'/api/referrals/{user_id}/history'
        if query_string:
            endpoint += f'?{query_string}'
        self.logger.debug(f'Getting referral history for user: {user_id}')
        return web.json_response(
            await self.panel.api_request('GET', endpoint)
        )

    async def _api_credit_points(self, request):
        """Credit points to user (proxy to Bot API)."""
        user_id = request.match_info['user_id']
        data = await request.json()
        self.logger.info(f'Crediting {data.get("amount")} points to user: {user_id}')
        return web.json_response(
            await self.panel.api_request(
                'POST',
                f'/api/referrals/{user_id}/points/credit',
                json=data
            )
        )

    async def _api_debit_points(self, request):
        """Debit points from user (proxy to Bot API)."""
        user_id = request.match_info['user_id']
        data = await request.json()
        self.logger.info(f'Debiting {data.get("amount")} points from user: {user_id}')
        return web.json_response(
            await self.panel.api_request(
                'POST',
                f'/api/referrals/{user_id}/points/debit',
                json=data
            )
        )
