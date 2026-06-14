# README FHIR API test URLs should mention Basic Auth when endpoint returns 401

Hi!

While using this template for the InterSystems AI Agents + FHIR Programming Contest, I noticed a small documentation mismatch in the README.

The README suggests testing the FHIR R4 API by opening:

```text
http://localhost:32783/fhir/r4/metadata
http://localhost:32783/fhir/r4/Patient/1
```

In my local Docker setup, unauthenticated requests returned:

```text
HTTP/1.1 401 Unauthorized
```

The same endpoints worked when Basic Auth was provided:

```powershell
curl.exe -i -u _SYSTEM:SYS http://localhost:32783/fhir/r4/metadata
curl.exe -i -u _SYSTEM:SYS http://localhost:32783/fhir/r4/Patient/1
```

Suggested README improvement:

- mention that the FHIR endpoint may require Basic Auth,
- include example curl commands with `-u _SYSTEM:SYS`,
- optionally mention checking the mapped host port with `docker ps`.

This would help first-time users verify the FHIR API more quickly.

Thank you!
