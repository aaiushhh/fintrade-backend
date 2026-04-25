import json
from app.main import app

def generate_markdown():
    openapi_schema = app.openapi()
    
    md = "# FItTrade LMS - Android Integration API Reference\n\n"
    md += "This document contains all API endpoints, request payloads, and response status codes, tailored for Android integration.\n\n"
    
    paths = openapi_schema.get("paths", {})
    
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method == "options": continue
            
            md += f"## `{method.upper()} {path}`\n\n"
            md += f"**Summary:** {operation.get('summary', 'No summary')}\n\n"
            
            # Request Body
            request_body = operation.get("requestBody")
            if request_body:
                content = request_body.get("content", {}).get("application/json")
                if content:
                    schema_ref = content.get("schema", {}).get("$ref")
                    md += "### Request Payload (JSON)\n"
                    if schema_ref:
                        schema_name = schema_ref.split("/")[-1]
                        md += f"- **Schema:** `{schema_name}`\n"
                        # We can resolve schema fields here
                        components = openapi_schema.get("components", {}).get("schemas", {})
                        schema = components.get(schema_name, {})
                        properties = schema.get("properties", {})
                        required = schema.get("required", [])
                        
                        md += "| Field | Type | Required | Description |\n"
                        md += "|---|---|---|---|\n"
                        for prop_name, prop_details in properties.items():
                            prop_type = prop_details.get("type", prop_details.get("anyOf", "unknown"))
                            is_req = "✅" if prop_name in required else "❌"
                            desc = prop_details.get("description", "")
                            if not isinstance(prop_type, str):
                                prop_type = str(prop_type)
                            md += f"| `{prop_name}` | {prop_type} | {is_req} | {desc} |\n"
                        md += "\n"
                    else:
                         md += "See OpenAPI JSON for inline schema.\n\n"
            
            # Parameters
            parameters = operation.get("parameters", [])
            if parameters:
                md += "### Parameters\n"
                md += "| Name | In | Type | Required | Description |\n"
                md += "|---|---|---|---|---|\n"
                for param in parameters:
                    name = param.get("name")
                    in_ = param.get("in")
                    req = "✅" if param.get("required") else "❌"
                    typ = param.get("schema", {}).get("type", "string")
                    desc = param.get("description", "")
                    md += f"| `{name}` | {in_} | {typ} | {req} | {desc} |\n"
                md += "\n"
            
            # Responses
            responses = operation.get("responses", {})
            md += "### Responses\n"
            md += "| Status | Description | Schema |\n"
            md += "|---|---|---|\n"
            for status, resp in responses.items():
                desc = resp.get("description", "")
                schema_name = "N/A"
                content = resp.get("content", {}).get("application/json", {})
                if content:
                    schema_ref = content.get("schema", {}).get("$ref")
                    if schema_ref:
                        schema_name = schema_ref.split("/")[-1]
                    else:
                        schema_name = "Inline/Any"
                md += f"| `{status}` | {desc} | `{schema_name}` |\n"
            md += "\n"
            md += "---\n\n"
            
    with open("docs/android_api_reference.md", "w", encoding="utf-8") as f:
        f.write(md)
        
    print("Generated docs/android_api_reference.md successfully.")

if __name__ == "__main__":
    generate_markdown()
