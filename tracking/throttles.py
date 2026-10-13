from rest_framework.throttling import SimpleRateThrottle


class PassengerLoginThrottle(SimpleRateThrottle):
    rate = "5/min"
    scope = "passenger-login"

    def get_cache_key(self, request, view):
        if request.method != "POST":
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class DriverLoginThrottle(PassengerLoginThrottle):
    scope = "driver-login"
