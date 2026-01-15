# Dictionary defining available API schemas
API_SCHEMAS = {
    "custom": {
        "name": "Custom API",
        "url": "",  # URL is provided by an input for custom requests
        "method": "GET",
        "doc_url": "https://httpbin.org/",
        "description": "Make custom HTTP requests to any endpoint",
        "category": "utility",
        "auth_type": "custom",
        # For custom, we use generic inputs. The block logic will treat them specially.
        "inputs": {
            "url": {
                "type": "string",
                "default": "https://httpbin.org/get",
                "required": True,
                "placeholder": "https://api.example.com/endpoint",
                "description": "The full URL for the API request"
            },
            "params": {
                "type": "json",
                "default": {},
                "placeholder": '{"key": "value"}',
                "description": "Query parameters as JSON object"
            },
            "body": {
                "type": "json",
                "default": {},
                "placeholder": '{"data": "value"}',
                "description": "Request body as JSON object"
            },
            "headers": {
                "type": "json",
                "default": {},
                "placeholder": '{"Authorization": "Bearer token"}',
                "description": "HTTP headers as JSON object"
            },
        },
        "outputs": {
            "response_json": {"type": "json", "description": "Parsed JSON response"},
            "status_code": {"type": "number", "description": "HTTP status code"}
        }
    },
    "cat_fact": {
        "name": "Cat Fact",
        "url": "https://catfact.ninja/fact",
        "method": "GET",
        "doc_url": "https://catfact.ninja/",
        "description": "Get random interesting cat facts",
        "category": "fun",
        "auth_type": "none",
        "rate_limit": "100/hour",
        "inputs": {},  # No inputs needed for this specific endpoint
        "outputs": {
            # These keys should match the API response for automatic mapping
            "fact": {"type": "string", "description": "A random cat fact"},
            "length": {"type": "number", "description": "Character length of the fact"}
        }
    },
    "agify": {
        "name": "Agify.io",
        "url": "https://api.agify.io",
        "method": "GET",
        "doc_url": "https://agify.io/",
        "description": "Predict age based on a person's name",
        "category": "fun",
        "auth_type": "none",
        "rate_limit": "1000/day",
        "inputs": {
            # This structure is now explicit. 'name' is a query parameter.
            "params": {
                "name": {
                    "type": "string",
                    "default": "michael",
                    "required": True,
                    "placeholder": "John",
                    "description": "First name to predict age for",
                    "validation": {
                        "min_length": 1,
                        "max_length": 255
                    }
                }
            }
        },
        "outputs": {
            "age": {"type": "number", "description": "Predicted age"},
            "count": {"type": "number", "description": "Number of data entries for this name"},
            "name": {"type": "string", "description": "The name that was analyzed"}
        }
    },
    "openai_chat": {
        "name": "OpenAI Responses API",
        "url": "https://api.openai.com/v1/responses",
        "method": "POST",
        "doc_url": "https://platform.openai.com/docs/api-reference/responses",
        "description": "Generate text responses using GPT models",
        "category": "ai",
        "auth_type": "api_key",
        "rate_limit": "500/min",
        "inputs": {
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_API_KEY",
                    "required": True,
                    "placeholder": "Bearer sk-...",
                    "description": "Your OpenAI API key"
                }
            },
            "body": {
                "model": {
                    "type": "string",
                    "default": "gpt-4",
                    "required": True,
                    "placeholder": "gpt-4",
                    "description": "The model to use for generation"
                },
                "input": {
                    "type": "string",
                    "default": "Tell me a three sentence bedtime story about a unicorn.",
                    "required": True,
                    "placeholder": "Enter your prompt...",
                    "description": "The prompt to send to the model",
                    "validation": {
                        "min_length": 1,
                        "max_length": 10000
                    }
                },
                "temperature": {"type": "number", "default": 1.0, "hidden": True, "description": "Sampling temperature (0-2)"},
                "top_p": {"type": "number", "default": 1.0, "hidden": True, "description": "Nucleus sampling parameter"},
                "max_output_tokens": {"type": "number", "default": None, "hidden": True, "description": "Maximum tokens to generate"},
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
        "description": "Convert addresses to geographic coordinates",
        "category": "data",
        "auth_type": "api_key",
        "rate_limit": "40000/day",
        "inputs": {
            "params": {
                "address": {
                    "type": "string",
                    "default": "1600 Amphitheatre Parkway, Mountain View, CA",
                    "required": True,
                    "placeholder": "123 Main St, City, State",
                    "description": "Street address to geocode"
                },
                "key": {
                    "type": "string",
                    "default": "YOUR_API_KEY",
                    "required": True,
                    "placeholder": "AIza...",
                    "description": "Google Cloud API key"
                }
            }
        },
        "outputs": {
            "results": {"type": "json", "description": "Geocoding results array"},
            "status": {"type": "string", "description": "API response status"}
        }
    },
    "airtable_list": {
        "name": "Airtable",
        "url": "https://api.airtable.com/v0/{base_id}/{table_name}",
        "method": "GET",
        "doc_url": "https://airtable.com/api",
        "description": "Read and manage database records",
        "category": "data",
        "auth_type": "bearer",
        "rate_limit": "5/sec",
        "inputs": {
            "path": {
                "base_id": {
                    "type": "string",
                    "default": "app...",
                    "required": True,
                    "placeholder": "appXXXXXXXXXXXXXX",
                    "description": "Airtable base ID"
                },
                "table_name": {
                    "type": "string",
                    "default": "Table 1",
                    "required": True,
                    "placeholder": "Table 1",
                    "description": "Name of the table to query"
                }
            },
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_TOKEN",
                    "required": True,
                    "placeholder": "Bearer pat...",
                    "description": "Airtable Personal Access Token"
                }
            }
        },
        "outputs": {
            "records": {"type": "json", "description": "Array of database records"}
        }
    },
    "twilio_send_sms": {
        "name": "Twilio: Send SMS",
        "doc_url": "https://www.twilio.com/docs/sms/api/message-resource",
        "description": "Send text messages programmatically",
        "url": "https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json",
        "method": "POST",
        "content_type": "application/x-www-form-urlencoded",
        "category": "communication",
        "auth_type": "basic",
        "rate_limit": "100/sec",
        "inputs": {
            "path": {
                "AccountSid": {
                    "type": "string",
                    "default": "",
                    "required": True,
                    "placeholder": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "description": "Twilio Account SID"
                }
            },
            "auth": {
                "AuthToken": {
                    "type": "string",
                    "default": "",
                    "required": True,
                    "placeholder": "Auth Token",
                    "description": "Twilio Auth Token"
                }
            },
            "body": {
                "To": {
                    "type": "string",
                    "default": "+1",
                    "required": True,
                    "placeholder": "+1234567890",
                    "description": "Recipient phone number with country code"
                },
                "From": {
                    "type": "string",
                    "default": "+1",
                    "required": True,
                    "placeholder": "+1234567890",
                    "description": "Twilio phone number to send from"
                },
                "Body": {
                    "type": "string",
                    "default": "Hello from Flow",
                    "required": True,
                    "placeholder": "Your message text...",
                    "description": "Message text content",
                    "validation": {
                        "max_length": 1600
                    }
                }
            }
        },
        "outputs": {
            "sid": {"type": "string", "path": "sid", "description": "Message SID"},
            "status": {"type": "string", "path": "status", "description": "Delivery status"},
            "error_code": {"type": "string", "path": "error_code", "description": "Error code if failed"},
            "error_message": {"type": "string", "path": "error_message", "description": "Error message if failed"}
        }
    },
    "mongodb_find": {
        "name": "MongoDB Atlas Find One",
        "url": "https://data.mongodb-api.com/app/{app_id}/endpoint/data/v1/action/findOne",
        "method": "POST",
        "doc_url": "https://www.mongodb.com/docs/atlas/app-services/data-api/openapi/",
        "description": "Query MongoDB databases for documents",
        "category": "data",
        "auth_type": "api_key",
        "rate_limit": "100/min",
        "inputs": {
            "path": {
                "app_id": {
                    "type": "string",
                    "default": "data-...",
                    "required": True,
                    "placeholder": "data-xxxxx",
                    "description": "MongoDB Data API App ID"
                }
            },
            "headers": {
                "api-key": {
                    "type": "string",
                    "default": "YOUR_API_KEY",
                    "required": True,
                    "placeholder": "API Key",
                    "description": "MongoDB Atlas API Key"
                }
            },
            "body": {
                "dataSource": {
                    "type": "string",
                    "default": "Cluster0",
                    "required": True,
                    "placeholder": "Cluster0",
                    "description": "Cluster name"
                },
                "database": {
                    "type": "string",
                    "default": "myDatabase",
                    "required": True,
                    "placeholder": "myDatabase",
                    "description": "Database name"
                },
                "collection": {
                    "type": "string",
                    "default": "myCollection",
                    "required": True,
                    "placeholder": "myCollection",
                    "description": "Collection name"
                },
                "filter": {
                    "type": "json",
                    "default": {},
                    "placeholder": '{"_id": "123"}',
                    "description": "Query filter as JSON object"
                }
            }
        },
        "outputs": {
            "document": {"type": "json", "description": "Found document or null"}
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
        "description": "Generate content with Gemini AI models",
        "category": "ai",
        "auth_type": "api_key",
        "rate_limit": "60/min",
        "inputs": {
            "path": {
                "model": {
                    "type": "string",
                    "default": "gemini-pro",
                    "required": True,
                    "placeholder": "gemini-pro",
                    "description": "Gemini model version"
                }
            },
            "params": {
                "key": {
                    "type": "string",
                    "default": "YOUR_API_KEY",
                    "required": True,
                    "placeholder": "AIza...",
                    "description": "Google AI API key"
                }
            },
            "body": {
                "contents": {
                    "type": "json",
                    "default": [{"parts": [{"text": "Write a story about a magic backpack"}]}],
                    "required": True,
                    "placeholder": '[{"parts": [{"text": "Your prompt"}]}]',
                    "description": "Content array with text prompts"
                }
            }
        },
        "outputs": {
            "text": {"type": "string", "path": "candidates.0.content.parts.0.text", "description": "Generated text response"},
            "response": {"type": "json", "description": "Full API response"}
        }
    },
    "anthropic_claude": {
        "name": "Anthropic API",
        "url": "https://api.anthropic.com/v1/messages",
        "method": "POST",
        "doc_url": "https://docs.anthropic.com/claude/reference/messages_post",
        "description": "Chat with Claude AI assistant",
        "category": "ai",
        "auth_type": "api_key",
        "rate_limit": "50/min",
        "inputs": {
            "headers": {
                "x-api-key": {
                    "type": "string",
                    "default": "YOUR_API_KEY",
                    "required": True,
                    "placeholder": "sk-ant-...",
                    "description": "Anthropic API key"
                },
                "anthropic-version": {
                    "type": "string",
                    "default": "2023-06-01",
                    "required": True,
                    "placeholder": "2023-06-01",
                    "description": "API version"
                }
            },
            "body": {
                "model": {
                    "type": "string",
                    "default": "claude-3-5-sonnet-20241022",
                    "required": True,
                    "placeholder": "claude-3-5-sonnet-20241022",
                    "description": "Claude model version"
                },
                "max_tokens": {
                    "type": "number",
                    "default": 1024,
                    "required": True,
                    "placeholder": "1024",
                    "description": "Maximum tokens to generate"
                },
                "messages": {
                    "type": "json",
                    "default": [{"role": "user", "content": "Hello, Claude"}],
                    "required": True,
                    "placeholder": '[{"role": "user", "content": "Your message"}]',
                    "description": "Conversation messages array"
                }
            }
        },
        "outputs": {
            "text": {"type": "string", "path": "content.0.text", "description": "Claude's response text"},
            "response": {"type": "json", "description": "Full API response"}
        }
    },
    "huggingface": {
        "name": "Hugging Face Inference",
        "url": "https://api-inference.huggingface.co/models/{model_id}",
        "method": "POST",
        "doc_url": "https://huggingface.co/docs/api-inference/index",
        "description": "Run ML models from Hugging Face Hub",
        "category": "ai",
        "auth_type": "bearer",
        "rate_limit": "1000/day",
        "inputs": {
            "path": {
                "model_id": {
                    "type": "string",
                    "default": "gpt2",
                    "required": True,
                    "placeholder": "gpt2",
                    "description": "Hugging Face model ID"
                }
            },
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_TOKEN",
                    "required": True,
                    "placeholder": "Bearer hf_...",
                    "description": "Hugging Face API token"
                }
            },
            "body": {
                "inputs": {
                    "type": "string",
                    "default": "The answer to the universe is",
                    "required": True,
                    "placeholder": "Your prompt...",
                    "description": "Input text for model inference"
                }
            }
        },
        "outputs": {
            "generated_text": {"type": "string", "path": "0.generated_text", "description": "Model-generated text"},
            "response": {"type": "json", "description": "Full API response"}
        }
    },
    "stability_ai": {
        "name": "Stability AI",
        "url": "https://api.stability.ai/v1/generation/{engine_id}/text-to-image",
        "method": "POST",
        "doc_url": "https://platform.stability.ai/docs/api-reference",
        "description": "Generate images from text prompts",
        "category": "ai",
        "auth_type": "bearer",
        "rate_limit": "150/min",
        "inputs": {
            "path": {
                "engine_id": {
                    "type": "string",
                    "default": "stable-diffusion-xl-1024-v1-0",
                    "required": True,
                    "placeholder": "stable-diffusion-xl-1024-v1-0",
                    "description": "Stability AI engine/model ID"
                }
            },
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_API_KEY",
                    "required": True,
                    "placeholder": "Bearer sk-...",
                    "description": "Stability AI API key"
                }
            },
            "body": {
                "text_prompts": {
                    "type": "json",
                    "default": [{"text": "A beautiful sunset over mountains"}],
                    "required": True,
                    "placeholder": '[{"text": "Your image description"}]',
                    "description": "Array of text prompts for image generation"
                },
                "cfg_scale": {
                    "type": "number",
                    "default": 7,
                    "placeholder": "7",
                    "description": "Prompt adherence scale (1-35)"
                },
                "height": {
                    "type": "number",
                    "default": 1024,
                    "placeholder": "1024",
                    "description": "Image height in pixels"
                },
                "width": {
                    "type": "number",
                    "default": 1024,
                    "placeholder": "1024",
                    "description": "Image width in pixels"
                },
                "samples": {
                    "type": "number",
                    "default": 1,
                    "placeholder": "1",
                    "description": "Number of images to generate"
                },
                "steps": {
                    "type": "number",
                    "default": 30,
                    "placeholder": "30",
                    "description": "Generation steps (quality)"
                }
            }
        },
        "outputs": {
            "image_base64": {"type": "string", "path": "artifacts.0.base64", "format": "base64_image", "description": "Base64-encoded image"},
            "artifacts": {"type": "json", "description": "All generated artifacts"}
        }
    },
    "elevenlabs": {
        "name": "ElevenLabs TTS",
        "url": "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        "method": "POST",
        "doc_url": "https://elevenlabs.io/docs/api-reference/text-to-speech",
        "description": "Convert text to realistic speech audio",
        "category": "ai",
        "auth_type": "api_key",
        "rate_limit": "20/min",
        "inputs": {
            "path": {
                "voice_id": {
                    "type": "string",
                    "default": "21m00Tcm4TlvDq8ikWAM",
                    "required": True,
                    "placeholder": "21m00Tcm4TlvDq8ikWAM",
                    "description": "ElevenLabs voice ID"
                }
            },
            "headers": {
                "xi-api-key": {
                    "type": "string",
                    "default": "YOUR_API_KEY",
                    "required": True,
                    "placeholder": "xi-api-key",
                    "description": "ElevenLabs API key"
                }
            },
            "body": {
                "text": {
                    "type": "string",
                    "default": "Hello! This is a test of text to speech.",
                    "required": True,
                    "placeholder": "Your text to speak...",
                    "description": "Text to convert to speech",
                    "validation": {
                        "max_length": 5000
                    }
                },
                "model_id": {
                    "type": "string",
                    "default": "eleven_monolingual_v1",
                    "placeholder": "eleven_monolingual_v1",
                    "description": "TTS model to use"
                },
                "voice_settings": {
                    "type": "json",
                    "default": {"stability": 0.5, "similarity_boost": 0.5},
                    "placeholder": '{"stability": 0.5, "similarity_boost": 0.5}',
                    "description": "Voice customization settings"
                }
            }
        },
        "outputs": {
            "audio_base64": {"type": "string", "format": "base64_audio", "description": "Base64-encoded audio file"},
            "content_type": {"type": "string", "description": "Audio MIME type"}
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
        "description": "Send messages to Slack channels",
        "category": "communication",
        "auth_type": "webhook",
        "rate_limit": "1/sec",
        "inputs": {
            "path": {
                "webhook_path": {
                    "type": "string",
                    "default": "T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
                    "required": True,
                    "placeholder": "T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX",
                    "description": "Slack webhook URL path"
                }
            },
            "body": {
                "text": {
                    "type": "string",
                    "default": "Hello from NodeLink!",
                    "required": True,
                    "placeholder": "Your message text...",
                    "description": "Message text to send to Slack"
                },
                "blocks": {
                    "type": "json",
                    "default": [],
                    "hidden": True,
                    "placeholder": '[]',
                    "description": "Slack Block Kit blocks (advanced)"
                }
            }
        },
        "outputs": {
            "status": {"type": "string", "description": "Webhook response status"}
        }
    },
    "discord_webhook": {
        "name": "Discord Webhook",
        "url": "{webhook_url}",
        "method": "POST",
        "doc_url": "https://discord.com/developers/docs/resources/webhook",
        "description": "Post messages to Discord channels",
        "category": "communication",
        "auth_type": "webhook",
        "rate_limit": "5/sec",
        "inputs": {
            "path": {
                "webhook_url": {
                    "type": "string",
                    "default": "https://discord.com/api/webhooks/...",
                    "required": True,
                    "placeholder": "https://discord.com/api/webhooks/123/abc",
                    "description": "Discord webhook URL"
                }
            },
            "body": {
                "content": {
                    "type": "string",
                    "default": "Hello World!",
                    "required": True,
                    "placeholder": "Your message...",
                    "description": "Message content",
                    "validation": {
                        "max_length": 2000
                    }
                },
                "username": {
                    "type": "string",
                    "default": "Protosynthesis",
                    "hidden": True,
                    "placeholder": "Bot Name",
                    "description": "Override webhook username"
                },
                "embeds": {
                    "type": "json",
                    "default": [],
                    "hidden": True,
                    "placeholder": '[]',
                    "description": "Discord embed objects"
                }
            }
        },
        "outputs": {
            "status": {"type": "string", "description": "Webhook response status"}
        }
    },
    "telegram_bot": {
        "name": "Telegram Bot API",
        "url": "https://api.telegram.org/bot{bot_token}/sendMessage",
        "method": "POST",
        "doc_url": "https://core.telegram.org/bots/api",
        "description": "Send messages via Telegram bots",
        "category": "communication",
        "auth_type": "token",
        "rate_limit": "30/sec",
        "inputs": {
            "path": {
                "bot_token": {
                    "type": "string",
                    "default": "YOUR_BOT_TOKEN",
                    "required": True,
                    "placeholder": "123456:ABC-DEF...",
                    "description": "Telegram bot token from BotFather"
                }
            },
            "body": {
                "chat_id": {
                    "type": "string",
                    "default": "CHAT_ID",
                    "required": True,
                    "placeholder": "123456789",
                    "description": "Target chat/channel ID"
                },
                "text": {
                    "type": "string",
                    "default": "Hello from NodeLink!",
                    "required": True,
                    "placeholder": "Your message...",
                    "description": "Message text",
                    "validation": {
                        "max_length": 4096
                    }
                },
                "parse_mode": {
                    "type": "string",
                    "default": "Markdown",
                    "hidden": True,
                    "placeholder": "Markdown",
                    "description": "Text formatting mode"
                }
            }
        },
        "outputs": {
            "message_id": {"type": "number", "path": "result.message_id", "description": "Sent message ID"},
            "response": {"type": "json", "description": "Full API response"}
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
        "description": "Process payments and create charges",
        "category": "payment",
        "auth_type": "bearer",
        "rate_limit": "100/sec",
        "inputs": {
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_SECRET_KEY",
                    "required": True,
                    "placeholder": "Bearer sk_...",
                    "description": "Stripe secret key"
                }
            },
            "body": {
                "amount": {
                    "type": "number",
                    "default": 2000,
                    "required": True,
                    "placeholder": "2000",
                    "description": "Amount in cents (e.g., 2000 = $20.00)"
                },
                "currency": {
                    "type": "string",
                    "default": "usd",
                    "required": True,
                    "placeholder": "usd",
                    "description": "Three-letter ISO currency code"
                },
                "source": {
                    "type": "string",
                    "default": "tok_visa",
                    "required": True,
                    "placeholder": "tok_visa",
                    "description": "Payment source token"
                },
                "description": {
                    "type": "string",
                    "default": "Charge for test@example.com",
                    "placeholder": "Charge description",
                    "description": "Charge description for records"
                }
            }
        },
        "outputs": {
            "id": {"type": "string", "description": "Charge ID"},
            "status": {"type": "string", "description": "Charge status"},
            "response": {"type": "json", "description": "Full charge object"}
        }
    },
    "paypal_payment": {
        "name": "PayPal",
        "url": "https://api-m.paypal.com/v2/checkout/orders",
        "method": "POST",
        "doc_url": "https://developer.paypal.com/docs/api/orders/v2/",
        "description": "Create and manage payment orders",
        "category": "payment",
        "auth_type": "bearer",
        "rate_limit": "50/sec",
        "inputs": {
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_ACCESS_TOKEN",
                    "required": True,
                    "placeholder": "Bearer A21AAxx...",
                    "description": "PayPal OAuth access token"
                }
            },
            "body": {
                "intent": {
                    "type": "string",
                    "default": "CAPTURE",
                    "required": True,
                    "placeholder": "CAPTURE",
                    "description": "Payment intent (CAPTURE or AUTHORIZE)"
                },
                "purchase_units": {
                    "type": "json",
                    "default": [{"amount": {"currency_code": "USD", "value": "100.00"}}],
                    "required": True,
                    "placeholder": '[{"amount": {"currency_code": "USD", "value": "100.00"}}]',
                    "description": "Array of purchase units with amounts"
                }
            }
        },
        "outputs": {
            "id": {"type": "string", "description": "Order ID"},
            "status": {"type": "string", "description": "Order status"},
            "response": {"type": "json", "description": "Full order object"}
        }
    },
    "exchange_rates": {
        "name": "Exchange Rates",
        "url": "https://openexchangerates.org/api/latest.json",
        "method": "GET",
        "doc_url": "https://docs.openexchangerates.org/",
        "description": "Get current currency exchange rates",
        "category": "data",
        "auth_type": "api_key",
        "rate_limit": "1000/month",
        "inputs": {
            "params": {
                "app_id": {
                    "type": "string",
                    "default": "YOUR_APP_ID",
                    "required": True,
                    "placeholder": "YOUR_APP_ID",
                    "description": "Open Exchange Rates App ID"
                },
                "base": {
                    "type": "string",
                    "default": "USD",
                    "placeholder": "USD",
                    "description": "Base currency code"
                }
            }
        },
        "outputs": {
            "rates": {"type": "json", "description": "Exchange rates object"},
            "base": {"type": "string", "description": "Base currency"},
            "timestamp": {"type": "number", "description": "Data timestamp"}
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
        "description": "Create and update Notion pages",
        "category": "productivity",
        "auth_type": "bearer",
        "rate_limit": "3/sec",
        "inputs": {
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_INTEGRATION_TOKEN",
                    "required": True,
                    "placeholder": "Bearer secret_...",
                    "description": "Notion integration token"
                },
                "Notion-Version": {
                    "type": "string",
                    "default": "2022-06-28",
                    "required": True,
                    "placeholder": "2022-06-28",
                    "description": "Notion API version"
                }
            },
            "body": {
                "parent": {
                    "type": "json",
                    "default": {"database_id": "YOUR_DATABASE_ID"},
                    "required": True,
                    "placeholder": '{"database_id": "YOUR_DATABASE_ID"}',
                    "description": "Parent database or page object"
                },
                "properties": {
                    "type": "json",
                    "default": {"Name": {"title": [{"text": {"content": "New Page"}}]}},
                    "required": True,
                    "placeholder": '{"Name": {"title": [{"text": {"content": "New Page"}}]}}',
                    "description": "Page properties object"
                }
            }
        },
        "outputs": {
            "id": {"type": "string", "description": "Page ID"},
            "url": {"type": "string", "description": "Page URL"},
            "response": {"type": "json", "description": "Full page object"}
        }
    },
    "google_sheets": {
        "name": "Google Sheets",
        "url": "https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range}:append",
        "method": "POST",
        "doc_url": "https://developers.google.com/sheets/api/reference/rest",
        "description": "Append data to Google Sheets",
        "category": "productivity",
        "auth_type": "api_key",
        "rate_limit": "60/min",
        "inputs": {
            "path": {
                "spreadsheet_id": {
                    "type": "string",
                    "default": "YOUR_SPREADSHEET_ID",
                    "required": True,
                    "placeholder": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                    "description": "Google Sheets spreadsheet ID"
                },
                "range": {
                    "type": "string",
                    "default": "Sheet1!A1",
                    "required": True,
                    "placeholder": "Sheet1!A1",
                    "description": "Target range (e.g., Sheet1!A1)"
                }
            },
            "params": {
                "key": {
                    "type": "string",
                    "default": "YOUR_API_KEY",
                    "required": True,
                    "placeholder": "AIza...",
                    "description": "Google Cloud API key"
                },
                "valueInputOption": {
                    "type": "string",
                    "default": "USER_ENTERED",
                    "required": True,
                    "placeholder": "USER_ENTERED",
                    "description": "Value input option"
                }
            },
            "body": {
                "values": {
                    "type": "json",
                    "default": [["Value 1", "Value 2", "Value 3"]],
                    "required": True,
                    "placeholder": '[["Value 1", "Value 2", "Value 3"]]',
                    "description": "2D array of values to append"
                }
            }
        },
        "outputs": {
            "updates": {"type": "json", "description": "Update summary object"},
            "spreadsheetId": {"type": "string", "description": "Spreadsheet ID"}
        }
    },
    "google_calendar": {
        "name": "Google Calendar",
        "url": "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
        "method": "POST",
        "doc_url": "https://developers.google.com/calendar/api/v3/reference/events/insert",
        "description": "Create calendar events and meetings",
        "category": "productivity",
        "auth_type": "oauth",
        "rate_limit": "10/sec",
        "inputs": {
            "path": {
                "calendar_id": {
                    "type": "string",
                    "default": "primary",
                    "required": True,
                    "placeholder": "primary",
                    "description": "Calendar ID (use 'primary' for main calendar)"
                }
            },
            "params": {
                "key": {
                    "type": "string",
                    "default": "YOUR_API_KEY",
                    "placeholder": "AIza...",
                    "description": "Google Cloud API key (optional with OAuth)"
                }
            },
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_ACCESS_TOKEN",
                    "required": True,
                    "placeholder": "Bearer ya29...",
                    "description": "OAuth 2.0 access token"
                }
            },
            "body": {
                "summary": {
                    "type": "string",
                    "default": "New Event",
                    "required": True,
                    "placeholder": "Meeting Title",
                    "description": "Event title/summary"
                },
                "start": {
                    "type": "json",
                    "default": {"dateTime": "2026-01-15T10:00:00-07:00"},
                    "required": True,
                    "placeholder": '{"dateTime": "2026-01-15T10:00:00-07:00"}',
                    "description": "Event start time object"
                },
                "end": {
                    "type": "json",
                    "default": {"dateTime": "2026-01-15T11:00:00-07:00"},
                    "required": True,
                    "placeholder": '{"dateTime": "2026-01-15T11:00:00-07:00"}',
                    "description": "Event end time object"
                }
            }
        },
        "outputs": {
            "id": {"type": "string", "description": "Event ID"},
            "htmlLink": {"type": "string", "description": "Calendar event URL"},
            "response": {"type": "json", "description": "Full event object"}
        }
    },
    "todoist": {
        "name": "Todoist",
        "url": "https://api.todoist.com/rest/v2/tasks",
        "method": "POST",
        "doc_url": "https://developer.todoist.com/rest/v2/#create-a-new-task",
        "description": "Create and manage tasks in Todoist",
        "category": "productivity",
        "auth_type": "bearer",
        "rate_limit": "450/15min",
        "inputs": {
            "headers": {
                "Authorization": {
                    "type": "string",
                    "default": "Bearer YOUR_API_TOKEN",
                    "required": True,
                    "placeholder": "Bearer 0123456789abcdef...",
                    "description": "Todoist API token"
                }
            },
            "body": {
                "content": {
                    "type": "string",
                    "default": "New task from NodeLink",
                    "required": True,
                    "placeholder": "Task description...",
                    "description": "Task content/description"
                },
                "project_id": {
                    "type": "string",
                    "default": "",
                    "hidden": True,
                    "placeholder": "2203306141",
                    "description": "Project ID (optional)"
                },
                "priority": {
                    "type": "number",
                    "default": 1,
                    "hidden": True,
                    "placeholder": "1",
                    "description": "Priority (1-4)"
                }
            }
        },
        "outputs": {
            "id": {"type": "string", "description": "Task ID"},
            "content": {"type": "string", "description": "Task content"},
            "response": {"type": "json", "description": "Full task object"}
        }
    }
}
