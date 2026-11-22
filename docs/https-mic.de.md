[English](https-mic.md) | Deutsch

# Sprechen im Browser (Mikrofon) über HTTPS

Sprechen zur Gegenstelle (`POST /answer` / **Sprechen**) benötigt einen **sicheren Ursprung** im Browser.
Über HTTP `http://homeassistant.local:8123` lässt sich das Mikrofon oft nicht verwenden.

## Empfohlene Wege

1. **NGINX Home Assistant SSL Proxy** (Add-on)  
   TLS am Proxy terminieren; HA über `https://…` öffnen. Diesen Weg verwenden, wenn bereits ein Zertifikat vorhanden ist oder ein Reverse-Proxy vor HA gewünscht ist.

2. **DuckDNS + Let’s Encrypt**  
   DuckDNS-Add-on (oder ähnlich) für einen Hostnamen + Let’s-Encrypt-Zertifikat verwenden und HA dann über `https://<your-duckdns>.duckdns.org:8123` aufrufen (oder über NGINX SSL Proxy mit diesen Zertifikaten).

Sobald HTTPS funktioniert, die Lovelace-Ansicht über diese HTTPS-URL öffnen und **Sprechen** verwenden. Kamera-Standbilder / Start / Stop benötigen kein Mikrofon.

## Reparatur: verbliebenes `http:` nach der Migration zur Oberfläche

Wenn die Einstellungen nach dem Umzug der HTTP-/Netzwerkkonfiguration in die Oberfläche beispielsweise **`yaml_still_present_after_migration`** anzeigen (oder sich Netzwerkeinstellungen nicht speichern lassen):

1. `configuration.yaml` öffnen.
2. Einen verbliebenen `http:`-Block auf oberster Ebene **entfernen**, sofern er Einstellungen dupliziert, die nun die Oberfläche verwaltet (z. B. `ssl_certificate`, `ssl_key`, `server_port`, `use_x_forwarded_for`, `trusted_proxies` nur dann, wenn diese in die Oberfläche / das Proxy-Add-on migriert wurden).
3. Proxy-bezogene Schlüssel nur dort beibehalten, wo der gewählte Weg sie benötigt (oft in der Konfiguration des NGINX-SSL-Proxy-Add-ons, nicht unter `http:` in Core).
4. Konfiguration prüfen → Home Assistant neu starten.

Kein unbeteiligtes YAML löschen. Nur die migrierten `http:`-Reste entfernen, auf die sich die Reparaturmeldung bezieht.
