The API can search users by email and phone values in keycloak. You can simply add another parameter, similar to the phone parameter. You only need to know the field name in the database.


Example:
```
curl -X GET "http://localhost:8000/api/jira_check?em=user@email.com" -H "Authorization: Bearer YOUR_TOKEN_FROM_MAIN_PY"
```

The response will return either
```
{"status":"ok","status_code":200}
```
or
```
{"status":"not found","status_code":404}
```
