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
     "twilio_send_sms": {
        "name": "Twilio: Send SMS",
        "doc_url": "https://www.twilio.com/docs/sms/api/message-resource",
        "url": "https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json",
        "method": "POST",
        "content_type": "application/x-www-form-urlencoded",
        "inputs": {
            "path": {
                "AccountSid": {"type": "string", "default": ""}
            },
            "headers": {
                "Authorization": {"type": "string", "default": "Basic <Base64 Credentials>"}
            },
            "body": {
                "To": {"type": "string", "default": "+1"},
                "From": {"type": "string", "default": "+1"},
                "Body": {"type": "string", "default": "Hello from Flow"}
            }
        },
        "outputs": {
            "sid": {"type": "string", "path": "sid"},
            "status": {"type": "string", "path": "status"},
            "error_code": {"type": "string", "path": "error_code"},
            "error_message": {"type": "string", "path": "error_message"}
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
    },
    # ============================================
    # AI/ML APIs
    # ============================================
    "google_gemini": {
        "name": "Google Gemini API",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "method": "POST",
        "doc_url": "https://ai.google.dev/api/rest",
        "inputs": {
            "path": {
                "model": {"type": "string", "default": "gemini-pro"}
            },
            "params": {
                "key": {"type": "string", "default": "YOUR_API_KEY"}
            },
            "body": {
                "contents": {"type": "json", "default": [{"parts": [{"text": "Write a story about a magic backpack"}]}]}
            }
        },
        "outputs": {
            "text": {"type": "string", "path": "candidates.0.content.parts.0.text"},
            "response": {"type": "json"}
        }
    },
    "anthropic_claude": {
        "name": "Anthropic Claude API",
        "url": "https://api.anthropic.com/v1/messages",
        "method": "POST",
        "doc_url": "https://docs.anthropic.com/claude/reference/messages_post",
        "inputs": {
            "headers": {
                "x-api-key": {"type": "string", "default": "YOUR_API_KEY"},
                "anthropic-version": {"type": "string", "default": "2023-06-01"}
            },
            "body": {
                "model": {"type": "string", "default": "claude-3-5-sonnet-20241022"},
                "max_tokens": {"type": "number", "default": 1024},
                "messages": {"type": "json", "default": [{"role": "user", "content": "Hello, Claude"}]}
            }
        },
        "outputs": {
            "text": {"type": "string", "path": "content.0.text"},
            "response": {"type": "json"}
        }
    },
    "huggingface": {
        "name": "Hugging Face Inference",
        "url": "https://api-inference.huggingface.co/models/{model_id}",
        "method": "POST",
        "doc_url": "https://huggingface.co/docs/api-inference/index",
        "inputs": {
            "path": {
                "model_id": {"type": "string", "default": "gpt2"}
            },
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_TOKEN"}
            },
            "body": {
                "inputs": {"type": "string", "default": "The answer to the universe is"}
            }
        },
        "outputs": {
            "generated_text": {"type": "string", "path": "0.generated_text"},
            "response": {"type": "json"}
        }
    },
    "stability_ai": {
        "name": "Stability AI",
        "url": "https://api.stability.ai/v1/generation/{engine_id}/text-to-image",
        "method": "POST",
        "doc_url": "https://platform.stability.ai/docs/api-reference",
        "inputs": {
            "path": {
                "engine_id": {"type": "string", "default": "stable-diffusion-xl-1024-v1-0"}
            },
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_API_KEY"}
            },
            "body": {
                "text_prompts": {"type": "json", "default": [{"text": "A beautiful sunset over mountains"}]},
                "cfg_scale": {"type": "number", "default": 7},
                "height": {"type": "number", "default": 1024},
                "width": {"type": "number", "default": 1024},
                "samples": {"type": "number", "default": 1},
                "steps": {"type": "number", "default": 30}
            }
        },
        "outputs": {
            "image_base64": {"type": "string", "path": "artifacts.0.base64"},
            "artifacts": {"type": "json"}
        }
    },
    "elevenlabs": {
        "name": "ElevenLabs TTS",
        "url": "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        "method": "POST",
        "doc_url": "https://elevenlabs.io/docs/api-reference/text-to-speech",
        "inputs": {
            "path": {
                "voice_id": {"type": "string", "default": "21m00Tcm4TlvDq8ikWAM"}
            },
            "headers": {
                "xi-api-key": {"type": "string", "default": "YOUR_API_KEY"}
            },
            "body": {
                "text": {"type": "string", "default": "Hello! This is a test of text to speech."},
                "model_id": {"type": "string", "default": "eleven_monolingual_v1"},
                "voice_settings": {"type": "json", "default": {"stability": 0.5, "similarity_boost": 0.5}}
            }
        },
        "outputs": {
            "audio_base64": {"type": "string"},
            "content_type": {"type": "string"}
        }
    },
    # ============================================
    # Communication APIs
    # ============================================
    "slack_webhook": {
        "name": "Slack Webhook",
        "url": "https://hooks.slack.com/services/{T00000000}/{B00000000}/{XXXXXXXXXXXXXXXXXXXX}",
        "method": "POST",
        "doc_url": "https://api.slack.com/messaging/webhooks",
        "inputs": {
            "path": {
                "webhook_path": {"type": "string", "default": "T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"}
            },
            "body": {
                "text": {"type": "string", "default": "Hello from NodeLink!"},
                "blocks": {"type": "json", "default": [], "hidden": True}
            }
        },
        "outputs": {
            "status": {"type": "string"}
        }
    },
    "discord_webhook": {
        "name": "Discord Webhook",
        "url": "{webhook_url}",
        "method": "POST",
        "doc_url": "https://discord.com/developers/docs/resources/webhook",
        "inputs": {
            "path": {
                "webhook_url": {"type": "string", "default": "https://discord.com/api/webhooks/..."}
            },
            "body": {
                "content": {"type": "string", "default": "Hello from NodeLink!"},
                "username": {"type": "string", "default": "NodeLink Bot", "hidden": True},
                "embeds": {"type": "json", "default": [], "hidden": True}
            }
        },
        "outputs": {
            "status": {"type": "string"}
        }
    },
    "telegram_bot": {
        "name": "Telegram Bot API",
        "url": "https://api.telegram.org/bot{bot_token}/sendMessage",
        "method": "POST",
        "doc_url": "https://core.telegram.org/bots/api",
        "inputs": {
            "path": {
                "bot_token": {"type": "string", "default": "YOUR_BOT_TOKEN"}
            },
            "body": {
                "chat_id": {"type": "string", "default": "CHAT_ID"},
                "text": {"type": "string", "default": "Hello from NodeLink!"},
                "parse_mode": {"type": "string", "default": "Markdown", "hidden": True}
            }
        },
        "outputs": {
            "message_id": {"type": "number", "path": "result.message_id"},
            "response": {"type": "json"}
        }
    },
    # ============================================
    # Payments & Finance APIs
    # ============================================
    "stripe_charge": {
        "name": "Stripe",
        "url": "https://api.stripe.com/v1/charges",
        "method": "POST",
        "doc_url": "https://stripe.com/docs/api/charges/create",
        "inputs": {
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_SECRET_KEY"}
            },
            "body": {
                "amount": {"type": "number", "default": 2000},
                "currency": {"type": "string", "default": "usd"},
                "source": {"type": "string", "default": "tok_visa"},
                "description": {"type": "string", "default": "Charge for test@example.com"}
            }
        },
        "outputs": {
            "id": {"type": "string"},
            "status": {"type": "string"},
            "response": {"type": "json"}
        }
    },
    "paypal_payment": {
        "name": "PayPal",
        "url": "https://api-m.paypal.com/v2/checkout/orders",
        "method": "POST",
        "doc_url": "https://developer.paypal.com/docs/api/orders/v2/",
        "inputs": {
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_ACCESS_TOKEN"}
            },
            "body": {
                "intent": {"type": "string", "default": "CAPTURE"},
                "purchase_units": {"type": "json", "default": [{"amount": {"currency_code": "USD", "value": "100.00"}}]}
            }
        },
        "outputs": {
            "id": {"type": "string"},
            "status": {"type": "string"},
            "response": {"type": "json"}
        }
    },
    "exchange_rates": {
        "name": "Exchange Rates",
        "url": "https://openexchangerates.org/api/latest.json",
        "method": "GET",
        "doc_url": "https://docs.openexchangerates.org/",
        "inputs": {
            "params": {
                "app_id": {"type": "string", "default": "YOUR_APP_ID"},
                "base": {"type": "string", "default": "USD"}
            }
        },
        "outputs": {
            "rates": {"type": "json"},
            "base": {"type": "string"},
            "timestamp": {"type": "number"}
        }
    },
    # ============================================
    # Productivity & Storage APIs
    # ============================================
    "notion_page": {
        "name": "Notion API",
        "url": "https://api.notion.com/v1/pages",
        "method": "POST",
        "doc_url": "https://developers.notion.com/reference/post-page",
        "inputs": {
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_INTEGRATION_TOKEN"},
                "Notion-Version": {"type": "string", "default": "2022-06-28"}
            },
            "body": {
                "parent": {"type": "json", "default": {"database_id": "YOUR_DATABASE_ID"}},
                "properties": {"type": "json", "default": {"Name": {"title": [{"text": {"content": "New Page"}}]}}}
            }
        },
        "outputs": {
            "id": {"type": "string"},
            "url": {"type": "string"},
            "response": {"type": "json"}
        }
    },
    "google_sheets": {
        "name": "Google Sheets",
        "url": "https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range}:append",
        "method": "POST",
        "doc_url": "https://developers.google.com/sheets/api/reference/rest",
        "inputs": {
            "path": {
                "spreadsheet_id": {"type": "string", "default": "YOUR_SPREADSHEET_ID"},
                "range": {"type": "string", "default": "Sheet1!A1"}
            },
            "params": {
                "key": {"type": "string", "default": "YOUR_API_KEY"},
                "valueInputOption": {"type": "string", "default": "USER_ENTERED"}
            },
            "body": {
                "values": {"type": "json", "default": [["Value 1", "Value 2", "Value 3"]]}
            }
        },
        "outputs": {
            "updates": {"type": "json"},
            "spreadsheetId": {"type": "string"}
        }
    },
    "google_calendar": {
        "name": "Google Calendar",
        "url": "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
        "method": "POST",
        "doc_url": "https://developers.google.com/calendar/api/v3/reference/events/insert",
        "inputs": {
            "path": {
                "calendar_id": {"type": "string", "default": "primary"}
            },
            "params": {
                "key": {"type": "string", "default": "YOUR_API_KEY"}
            },
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_ACCESS_TOKEN"}
            },
            "body": {
                "summary": {"type": "string", "default": "New Event"},
                "start": {"type": "json", "default": {"dateTime": "2026-01-15T10:00:00-07:00"}},
                "end": {"type": "json", "default": {"dateTime": "2026-01-15T11:00:00-07:00"}}
            }
        },
        "outputs": {
            "id": {"type": "string"},
            "htmlLink": {"type": "string"},
            "response": {"type": "json"}
        }
    },
    "todoist": {
        "name": "Todoist",
        "url": "https://api.todoist.com/rest/v2/tasks",
        "method": "POST",
        "doc_url": "https://developer.todoist.com/rest/v2/#create-a-new-task",
        "inputs": {
            "headers": {
                "Authorization": {"type": "string", "default": "Bearer YOUR_API_TOKEN"}
            },
            "body": {
                "content": {"type": "string", "default": "New task from NodeLink"},
                "project_id": {"type": "string", "default": "", "hidden": True},
                "priority": {"type": "number", "default": 1, "hidden": True}
            }
        },
        "outputs": {
            "id": {"type": "string"},
            "content": {"type": "string"},
            "response": {"type": "json"}
        }
    }
}
