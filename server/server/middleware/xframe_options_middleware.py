class XFrameOptionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Allow embedding from the Amplify domains
        response['X-Frame-Options'] = 'ALLOW-FROM https://main.d1lwa086vbiduv.amplifyapp.com https://main.d8zzmpev39qs6.amplifyapp.com'
        return response
