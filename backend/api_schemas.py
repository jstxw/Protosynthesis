# Dictionary defining available API schemas
API_SCHEMAS = {
    "custom": {
        "name": "Custom API",
        "url": "", # URL is provided by an input for custom requests
        "method": "GET",
        "doc_url": "https://httpbin.org/",
        # For custom, we use generic inputs. The block logic will treat them specially.
        "inputs": {
            "url": {"type": "string", "default": "https://httpbin.org/get"},
            "params": {"type": "json", "default": {}},
            "body": {"type": "json", "default": {}},
            "headers": {"type": "json", "default": {}},
        },
        "outputs": {
            "response_json": {"type": "json"},
            "status_code": {"type": "number"}
        }
    },
    "cat_fact": {
        "name": "Cat Fact",
        "url": "https://catfact.ninja/fact",
        "method": "GET",
        "doc_url": "https://catfact.ninja/",
        "inputs": {}, # No inputs needed for this specific endpoint
        "outputs": {
            # These keys should match the API response for automatic mapping
            "fact": {"type": "string"},
            "length": {"type": "number"}
        }
    },
    "agify": {
        "name": "Agify.io",
        "url": "https://api.agify.io",
        "method": "GET",
        "doc_url": "https://agify.io/",
        "inputs": {
            # This structure is now explicit. 'name' is a query parameter.
            "params": {
                "name": {"type": "string", "default": "michael"}
            }
        },
        "outputs": {
            "age": {"type": "number"},
            "count": {"type": "number"},
            "name": {"type": "string"}
        }
    },
    "openai_chat": {
        "name": "OpenAI Responses API",
        "url": "https://api.openai.com/v1/responses",
        "method": "POST",
        "doc_url": "https://platform.openai.com/docs/api-reference/responses",
        "inputs": {
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_API_KEY"}
            },
            "body": {
                "model": {"type": "string", "default": "gpt-4.1"},
                "input": {"type": "string", "default": "Tell me a three sentence bedtime story about a unicorn."},
                "temperature": {"type": "number", "default": 1.0, "hidden": True},
                "top_p": {"type": "number", "default": 1.0, "hidden": True},
                "max_output_tokens": {"type": "number", "default": None, "hidden": True},
                "store": {"type": "boolean", "default": True, "hidden": True},
                "metadata": {"type": "json", "default": {}, "hidden": True}
            }
        },
        "outputs": {
            "message_text": {"type": "string", "path": "output.0.content.0.text"},
            "output_full": {"type": "json", "path": "output"},
            "usage": {"type": "json"},
            "id": {"type": "string", "hidden": True},
            "status": {"type": "string", "hidden": True},
            "model": {"type": "string", "hidden": True},
            "created_at": {"type": "number", "hidden": True}
        }
    },
    "google_maps_geocode": {
        "name": "Google Maps Data",
        "url": "https://maps.googleapis.com/maps/api/geocode/json",
        "method": "GET",
        "doc_url": "https://developers.google.com/maps/documentation/geocoding/overview",
        "inputs": {
            "params": {
                "address": {"type": "string", "default": "1600 Amphitheatre Parkway, Mountain View, CA"},
                "key": {"type": "string", "default": "YOUR_API_KEY"}
            }
        },
        "outputs": {
            "results": {"type": "json"},
            "status": {"type": "string"}
        }
    },
    "airtable_list": {
        "name": "Airtable",
        "url": "https://api.airtable.com/v0/{base_id}/{table_name}",
        "method": "GET",
        "doc_url": "https://airtable.com/api",
        "inputs": {
            "path": {
                "base_id": {"type": "string", "default": "app..."},
                "table_name": {"type": "string", "default": "Table 1"}
            },
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_TOKEN"}
            }
        },
        "outputs": {
            "records": {"type": "json"}
        }
    },
    "twilio_sms": {
        "name": "Twilio Send SMS",
        "url": "https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json",
        "method": "POST",
        "doc_url": "https://www.twilio.com/docs/sms/api/message-resource",
        "inputs": {
            "path": {
                "AccountSid": {"type": "string", "default": "AC..."}
            },
            "headers": {
                "Authorization": {"type": "string", "default": "Basic base64(SID:TOKEN)"}
            },
            "body": {
                "To": {"type": "string", "default": "+1..."},
                "From": {"type": "string", "default": "+1..."},
                "Body": {"type": "string", "default": "Hello from Flow Builder"}
            }
        },
        "outputs": {
            "sid": {"type": "string"},
            "status": {"type": "string"}
        }
    },
    "mongodb_find": {
        "name": "MongoDB Atlas Find One",
        "url": "https://data.mongodb-api.com/app/{app_id}/endpoint/data/v1/action/findOne",
        "method": "POST",
        "doc_url": "https://www.mongodb.com/docs/atlas/app-services/data-api/openapi/",
        "inputs": {
            "path": {
                "app_id": {"type": "string", "default": "data-..."}
            },
            "headers": {
                "api-key": {"type": "string", "default": "YOUR_API_KEY"}
            },
            "body": {
                "dataSource": {"type": "string", "default": "Cluster0"},
                "database": {"type": "string", "default": "myDatabase"},
                "collection": {"type": "string", "default": "myCollection"},
                "filter": {"type": "json", "default": {}}
            }
        },
        "outputs": {
            "document": {"type": "json"}
        }
    }
}
