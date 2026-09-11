import json
import os
import subprocess
import litellm
try:
    from system_diagnostics import SystemDiagnostics
except ImportError:  # pragma: no cover - compatibility when importing from project root
    from nia_agent.system_diagnostics import SystemDiagnostics
from desktop_tools import DesktopTools
from browser_tools import BrowserTools
from project_indexer import ProjectIndexer
from code_workspace import CodeWorkspace
from git_review import GitReview
from project_validator import ProjectValidator
from ast_indexer import PythonASTIndexer

class NiaAgentOrchestrator:
    def __init__(self, config: dict):
        self.config = config
        self.user_name = config["user_profile"]["name"]
        self.whatsapp_num = config["user_profile"]["whatsapp_number"]
        self.diagnostics = SystemDiagnostics(
            config,
            log_dir=os.path.join(os.path.dirname(__file__), "logs")
        )
        
        api_key = config["api_keys"].get("gemini_api_key") or config["api_keys"].get("openai_api_key")
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ["OPENAI_API_KEY"] = api_key
            litellm.api_key = api_key
            
        self.desktop = DesktopTools(config["system_paths"]["projects_dir"])
        self.browser = BrowserTools(config["system_paths"]["whatsapp_session_dir"])
        self.project_indexer = ProjectIndexer(config["system_paths"]["projects_dir"])
        self.code_workspace = CodeWorkspace(config["system_paths"]["projects_dir"])
        self.git_review = GitReview(config["system_paths"]["projects_dir"])
        self.project_validator = ProjectValidator(config["system_paths"]["projects_dir"])
        self.ast_indexer = PythonASTIndexer(config["system_paths"]["projects_dir"])
        
        from memory_manager import MemoryManager
        self.memory = MemoryManager(os.path.join(os.path.dirname(__file__), "memory_bank.json"))
        
        # Tools definitions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Opens applications like notepad, chrome, calculator, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {"app_name": {"type": "string"}},
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_vscode_project",
                    "description": "Opens a web development project in VS Code.",
                    "parameters": {
                        "type": "object",
                        "properties": {"project_name": {"type": "string"}},
                        "required": ["project_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "play_song",
                    "description": "Plays music or audio. Uses Windows Media Player as the default player for all songs. Only uses YouTube if the user explicitly asks for YouTube.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "song_name": {"type": "string", "description": "The song title, artist, or query."},
                            "platform": {
                                "type": "string",
                                "enum": ["windows_media_player", "youtube"],
                                "description": "Target player: 'windows_media_player' (default) or 'youtube' (only when explicitly mentioned)."
                            }
                        },
                        "required": ["song_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_url",
                    "description": "Opens a web address or URL in browser.",
                    "parameters": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "take_and_send_screenshot",
                    "description": "Takes a desktop screenshot and sends it to the user's registered WhatsApp.",
                    "parameters": {
                        "type": "object",
                        "properties": {"caption": {"type": "string"}}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_whatsapp_message",
                    "description": "Sends a WhatsApp text to a specific phone number or registered owner.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "target_number": {"type": "string", "description": "Optional phone number. Defaults to registered owner."}
                        },
                        "required": ["message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "draft_document",
                    "description": "Drafts letters, official documents, or memos.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "doc_type": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["title", "doc_type", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "system_power_control",
                    "description": "Shuts down or restarts the computer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["shutdown", "restart", "cancel"]}
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "remember_fact",
                    "description": "Saves a new fact to the user's permanent memory bank. Use this whenever the user asks you to remember something or provides a personal preference.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "The category or subject (e.g. 'family', 'work', 'preferences')"},
                            "fact": {"type": "string", "description": "The specific detail to remember"}
                        },
                        "required": ["topic", "fact"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_project_file",
                    "description": "Read a UTF-8 source file from the configured project using a relative path. Read-only.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string"}
                        },
                        "required": ["relative_path"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "preview_file_change",
                    "description": "Generate a unified diff for one exact text replacement without changing any file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string"},
                            "old_text": {"type": "string"},
                            "new_text": {"type": "string"}
                        },
                        "required": ["relative_path", "old_text", "new_text"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_file_change",
                    "description": "Apply one exact reviewed replacement after explicit confirmation. Creates a backup first.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string"},
                            "old_text": {"type": "string"},
                            "new_text": {"type": "string"},
                            "confirm": {"type": "boolean", "description": "Must be true only after the user approved the preview."}
                        },
                        "required": ["relative_path", "old_text", "new_text", "confirm"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "review_git_changes",
                    "description": "Read-only Git status and unstaged diff review. Never stages, commits, or changes files.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "commit_git_changes",
                    "description": "Stage selected safe project paths and create a local Git commit after explicit approval. Never pushes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "paths": {"type": "array", "items": {"type": "string"}},
                            "confirm": {"type": "boolean", "description": "Must be true only after review_git_changes and user approval."}
                        },
                        "required": ["message", "paths", "confirm"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "preview_multi_file_change",
                    "description": "Generate one unified diff for exact replacements across multiple project files without changing them.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "changes": {"type": "array", "items": {"type": "object"}}
                        },
                        "required": ["changes"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_multi_file_change",
                    "description": "Apply an exact reviewed multi-file replacement plan after explicit confirmation. Creates backups and never commits.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "changes": {"type": "array", "items": {"type": "object"}},
                            "confirm": {"type": "boolean", "description": "Must be true only after the preview was reviewed and approved."}
                        },
                        "required": ["changes", "confirm"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_project",
                    "description": "Run bounded project validation checks, currently Python compilation, without changing Git state.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "inspect_project",
                    "description": "Read-only inventory of the configured project: source files, extensions, sizes, and ignored directories.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "inspect_code_symbols",
                    "description": "Read-only Python AST inspection that returns classes, functions, imports, and line numbers for a file or the configured project.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string", "description": "Optional project-relative Python file to inspect."}
                        },
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "inspect_project_structure",
                    "description": "Read-only structured inspection for JavaScript, TypeScript, JSON, HTML, and CSS files using lightweight parsing.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {"type": "string", "description": "Project-relative file path for the structure inspection."}
                        },
                        "required": ["relative_path"],
                        "additionalProperties": False
                    }
                }
            }
        ]

    def get_system_prompt(self) -> str:
        mem_ctx = self.memory.get_all_context()
        return f"""You are Nia, a highly capable desktop AI agent and personal assistant to {self.user_name}.
Your memory bank:
{mem_ctx}

Your persona rules:
1. Always address the user warmly in conversational Hindi or Hinglish (e.g. "Haan {self.user_name} ji, main abhi kar deti hoon", "Maine document draft kar diya hai").
2. Your voice engine is Microsoft Swara Neural, so write phonetically natural Hinglish/Hindi text without robotic tone.
3. You can execute local actions (launching apps, opening VS Code projects, taking screenshots, playing music, sending WhatsApp messages, drafting letters).
4. When a tool finishes executing, summarize the result politely in 1-2 Hinglish sentences.
5. For requests about project files or code structure, use inspect_project and read_project_file before suggesting changes. Use preview_file_change or preview_multi_file_change before any modification, and require explicit user approval before apply_file_change or apply_multi_file_change with confirm=true.
6. After applying code changes, use validate_project before reviewing or committing them.
7. For Git requests, use review_git_changes first. Never stage or commit without explicit user approval. Never push automatically.
8. Default music player is Windows Media Player for all songs and music. ONLY open YouTube if the user explicitly specifies 'YouTube'. When playing on YouTube, Nia always plays the first song automatically."""

    def analyze_screen(self, query: str) -> str:
        """Takes a screenshot and sends it to a vision-capable LLM to answer the user's query."""
        import base64
        try:
            # 1. Take the screenshot
            img_path = self.desktop.take_screenshot("vision_capture")
            
            # 2. Base64 encode it
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
                
            # 3. Create messages payload
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Look at my screen and answer in Hinglish: {query}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_data}"
                            }
                        }
                    ]
                }
            ]
            
            # Use gemini flash or a vision-capable model
            # Note: We hardcode gemini flash here or fallback to openai because ollama vision support can be tricky via LiteLLM without a specific model like llava.
            model_to_use = self.config.get("llm_settings", {}).get("vision_model", "gemini/gemini-3.6-flash")
            completion_options = {"timeout": 30}
            if model_to_use.startswith("ollama/"):
                completion_options["api_base"] = self.config.get("llm_settings", {}).get("base_url")
            
            response = litellm.completion(
                model=model_to_use,
                messages=messages,
                **completion_options
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Screen analyze karte samay ek error aayi: {str(e)}"

    def process_command(self, user_input: str) -> str:
        user_input = user_input.strip()
        if user_input.lower() in {"check system status", "system status", "check diagnostics", "run diagnostics"}:
            return self.diagnostics.get_status_summary()

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": user_input}
        ]
        
        # Read configured model
        llm_model = self.config.get("llm_settings", {}).get("model", "gemini/gemini-3.6-flash")
        completion_options = {"timeout": 12}
        if llm_model.startswith("ollama/"):
            completion_options["api_base"] = self.config.get("llm_settings", {}).get("base_url")
        
        try:
            response = litellm.completion(
                model=llm_model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                **completion_options
            )
        except Exception as e:
            print(f"[Nia LLM Fallback Triggered using model '{llm_model}']: {e}")
            return self._fallback_local_intent(user_input)

        choice = response.choices[0].message
        
        # If model decided to call tools
        if choice.tool_calls:
            tool_outputs = []
            for tool_call in choice.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"[Nia Tool Dispatch]: Executing {fn_name}({fn_args})")
                
                result = self._execute_tool(fn_name, fn_args)
                tool_outputs.append(f"{fn_name} result: {result}")
            
            # Follow-up completion for verbal Hinglish summary
            try:
                follow_up = litellm.completion(
                    model=llm_model,
                    messages=messages + [
                        choice,
                        {"role": "tool", "name": fn_name, "content": " | ".join(tool_outputs), "tool_call_id": tool_call.id}
                    ],
                    **completion_options
                )
                return follow_up.choices[0].message.content
            except Exception:
                return " | ".join(tool_outputs)
        else:
            return choice.content

    def _fallback_local_intent(self, user_input: str) -> str:
        c = user_input.lower().strip()
        from datetime import datetime

        if any(w in c for w in ("hello", "hi", "namaste", "hey", "नमस्ते")):
            return f"Namaste {self.user_name} ji! Main Nia hoon. Main aapki kya madad kar sakti hoon?"
        elif any(w in c for w in ("kaise ho", "kya haal", "how are you")):
            return "Main bilkul theek hoon! Aap batayein, aaj computer me kya kaam karna hai?"
        elif any(w in c for w in ("samay", "time", "date", "tarikh", "din", "waqt")):
            now = datetime.now()
            return f"Abhi samay hai: {now.strftime('%I:%M %p')}, aur date hai: {now.strftime('%d %B %Y')}."
        elif any(w in c for w in ("who are you", "kaun ho", "kya kar sakti ho")):
            return f"Main Nia hoon, {self.user_name} ji ki personal desktop AI assistant. Main apps khol sakti hoon, gaane chala sakti hoon, WhatsApp handle karti hoon aur computer control karti hoon."
        
        # Real local tool execution fallbacks
        if any(k in c for k in ("calc", "calculator", "कैलकुलेटर")):
            self.desktop.open_application("calculator")
            return "Calculator open kar diya hai."
        elif any(k in c for k in ("notepad", "नोटपैड")):
            self.desktop.open_application("notepad")
            return "Notepad open kar diya hai."
        elif any(k in c for k in ("chrome", "browser", "क्रोम")):
            self.desktop.open_application("chrome")
            return "Google Chrome open kar diya hai."
        elif any(k in c for k in ("paint", "mspaint", "पेंट")):
            self.desktop.open_application("mspaint")
            return "MS Paint open kar diya hai."
        elif any(k in c for k in ("vs code", "vscode")):
            self.desktop.open_application("code")
            return "Visual Studio Code launch kar diya hai."
        elif any(k in c for k in ("taskmgr", "task manager")):
            self.desktop.open_application("taskmgr")
            return "Task Manager open kar diya hai."
        elif any(k in c for k in ("explorer", "files", "my computer")):
            self.desktop.open_application("explorer")
            return "File Explorer open kar diya hai."
        elif any(k in c for k in ("screenshot", "screen shot", "स्क्रीनशॉट")):
            path = self.desktop.take_screenshot()
            return f"Screenshot le liya hai: {os.path.basename(path)}."
        elif any(k in c for k in ("play", "gana", "gaana", "song", "music", "bajao", "गाना")):
            if "youtube" in c:
                clean = c.replace("on youtube", "").replace("youtube", "").replace("play", "").strip()
                return self.browser.play_song(clean or "popular songs")
            else:
                clean = c
                for word in ("open", "launch", "start", "play", "song", "music", "gana", "gaana", "bajao"):
                    clean = clean.replace(word, " ")
                clean = " ".join(clean.split())
                return self.desktop.play_in_windows_media_player(clean)
        elif "shutdown" in c:
            return self.desktop.system_power_control("shutdown")
        elif "restart" in c or "reboot" in c:
            return self.desktop.system_power_control("restart")

        return f"Namaste {self.user_name} ji! Main aapke desktop commands (jaise open notepad, calculator, chrome, songs, screenshot) directly chala sakti hoon. Aap batayein kya open karna hai?"

    def _execute_tool(self, name: str, args: dict) -> str:
        if name == "open_application":
            return self.desktop.open_application(args.get("app_name"))
        elif name == "open_vscode_project":
            return self.desktop.open_vscode_project(args.get("project_name"))
        elif name == "play_song":
            song = args.get("song_name", "")
            platform = str(args.get("platform", "")).lower()
            if platform == "youtube" or "youtube" in song.lower():
                clean = song.replace("on youtube", "").replace("in youtube", "").replace("youtube", "").strip()
                return self.browser.play_song(clean or song)
            else:
                clean = song.replace("music", "").replace("song", "").strip()
                return self.desktop.play_in_windows_media_player(clean or song)
        elif name == "open_url":
            return self.desktop.open_url(args.get("url"))
        elif name == "take_and_send_screenshot":
            filepath = self.desktop.take_screenshot()
            target_phone = self.whatsapp_num
            return self.browser.send_whatsapp_screenshot(target_phone, filepath, args.get("caption", "Screenshot"))
        elif name == "send_whatsapp_message":
            target = args.get("target_number") or self.whatsapp_num
            return self.browser.send_whatsapp_message(target, args.get("message"))
        elif name == "draft_document":
            return self.desktop.draft_document(args.get("title"), args.get("doc_type"), args.get("content"))
        elif name == "system_power_control":
            return self.desktop.system_power_control(args.get("action"))
        elif name == "remember_fact":
            return self.memory.remember(args.get("topic", "general"), args.get("fact"))
        elif name == "inspect_project":
            return self.project_indexer.format_summary()
        elif name == "inspect_code_symbols":
            relative_path = args.get("relative_path")
            try:
                return self.ast_indexer.format_summary(relative_path) if relative_path else self.ast_indexer.format_summary()
            except (FileNotFoundError, ValueError, OSError) as exc:
                return f"Python symbol inspection error: {exc}"
        elif name == "inspect_project_structure":
            try:
                return str(self.project_indexer.inspect_file_structure(args.get("relative_path", "")))
            except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError) as exc:
                return f"Project structure inspection error: {exc}"
        elif name == "read_project_file":
            try:
                return self.code_workspace.read_file(args.get("relative_path", ""))
            except (FileNotFoundError, ValueError) as exc:
                return f"Project read error: {exc}"
        elif name == "preview_file_change":
            try:
                return self.code_workspace.preview_change(
                    args.get("relative_path", ""),
                    args.get("old_text", ""),
                    args.get("new_text", ""),
                )
            except (FileNotFoundError, ValueError) as exc:
                return f"Change preview error: {exc}"
        elif name == "apply_file_change":
            try:
                return self.code_workspace.apply_change(
                    args.get("relative_path", ""),
                    args.get("old_text", ""),
                    args.get("new_text", ""),
                    bool(args.get("confirm", False)),
                )
            except (FileNotFoundError, ValueError, OSError) as exc:
                return f"Change apply error: {exc}"
        elif name == "review_git_changes":
            return self.git_review.review()
        elif name == "commit_git_changes":
            try:
                return self.git_review.commit(
                    args.get("message", ""),
                    args.get("paths", []),
                    bool(args.get("confirm", False)),
                )
            except (RuntimeError, ValueError, OSError) as exc:
                return f"Git commit error: {exc}"
        elif name == "validate_project":
            try:
                return self.project_validator.validate()
            except (OSError, subprocess.TimeoutExpired) as exc:
                return f"Project validation error: {exc}"
        elif name == "preview_multi_file_change":
            try:
                return self.code_workspace.preview_multi_change(args.get("changes", []))
            except (FileNotFoundError, ValueError) as exc:
                return f"Multi-file preview error: {exc}"
        elif name == "apply_multi_file_change":
            try:
                return self.code_workspace.apply_multi_change(
                    args.get("changes", []),
                    bool(args.get("confirm", False)),
                )
            except (FileNotFoundError, ValueError, OSError) as exc:
                return f"Multi-file apply error: {exc}"
        return f"Unknown function {name}"

