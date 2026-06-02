import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("GITHUB_API_KEY", "test")
os.environ.setdefault("CLERK_WEBHOOK_SECRET", "test")
os.environ.setdefault("JWT_PUBLIK_KEY", "test")
os.environ.setdefault("CLEERK_SCERET_KEY", "test")

from app.services.code_store import build_extraction_payload


def _by_full_name(chunks):
    return {chunk.fullName: chunk for chunk in chunks}


class SemanticChunkTests(unittest.TestCase):
    def test_python_chunks_are_semantic_and_connected(self):
        payload = build_extraction_payload(
            "repo-1",
            [
                {
                    "path": "services/helpers.py",
                    "content": 'def helper():\n    return "ok"\n',
                },
                {
                    "path": "app/service.py",
                    "content": (
                        "from services.helpers import helper\n\n"
                        "class Greeter:\n"
                        "    \"\"\"Coordinates greetings.\"\"\"\n"
                        "    def greet(self, name):\n"
                        "        \"\"\"Build greeting.\"\"\"\n"
                        "        helper()\n"
                        "        self._format(name)\n"
                        "        missing_call()\n"
                        "        return name\n\n"
                        "    def _format(self, name):\n"
                        "        return name.upper()\n"
                    ),
                },
            ],
        )

        chunks = _by_full_name(payload["chunk_rows"])
        greeter = chunks["app.service.Greeter"]
        greet = chunks["app.service.Greeter.greet"]
        helper = chunks["services.helpers.helper"]

        self.assertEqual(greeter.metadataJson["semanticKind"], "class")
        self.assertEqual(greeter.metadataJson["docstring"], "Coordinates greetings.")
        self.assertEqual(greet.metadataJson["semanticKind"], "method")
        self.assertEqual(greet.metadataJson["docstring"], "Build greeting.")
        self.assertEqual(greet.parentChunkId, greeter.id)
        self.assertTrue(greeter.content.startswith("class Greeter:"))
        self.assertTrue(greet.content.strip().startswith("def greet"))
        self.assertNotIn("class Greeter:", greet.content)
        self.assertIn("contentHash", greet.metadataJson)

        connections = payload["connection_rows"]
        import_edges = [edge for edge in connections if edge.connectionType == "import"]
        call_edges = [edge for edge in connections if edge.connectionType == "call"]

        self.assertTrue(any(
            edge.targetPath == "services/helpers.py" and edge.confidence == "resolved"
            for edge in import_edges
        ))
        self.assertTrue(any(
            edge.targetSymbol == "helper"
            and edge.targetChunkId == helper.id
            and edge.confidence == "resolved"
            for edge in call_edges
        ))
        self.assertTrue(any(
            edge.targetSymbol == "missing_call"
            and edge.targetChunkId is None
            and edge.confidence == "unresolved"
            for edge in call_edges
        ))
        self.assertEqual(
            greet.metadataJson["unresolvedCalls"],
            [{"calleeText": "missing_call", "line": 9}],
        )

    def test_typescript_chunks_capture_exports_and_source(self):
        payload = build_extraction_payload(
            "repo-2",
            [
                {
                    "path": "src/helpers.ts",
                    "content": "export function helper() {\n  return true;\n}\n",
                },
                {
                    "path": "src/controller.ts",
                    "content": (
                        "import { helper } from './helpers';\n\n"
                        "export class Controller {\n"
                        "  run() {\n"
                        "    helper();\n"
                        "    unknown();\n"
                        "  }\n"
                        "}\n\n"
                        "export const makeController = () => new Controller();\n"
                    ),
                },
            ],
        )

        chunks = _by_full_name(payload["chunk_rows"])
        controller = chunks["src.controller.Controller"]
        run = chunks["src.controller.Controller.run"]

        self.assertEqual(controller.metadataJson["language"], "typescript")
        self.assertEqual(controller.metadataJson["semanticKind"], "class")
        self.assertIn("src.controller.Controller", controller.metadataJson["exports"])
        self.assertEqual(run.parentChunkId, controller.id)
        self.assertTrue(run.content.strip().startswith("run()"))

        self.assertTrue(any(
            edge.connectionType == "call"
            and edge.targetSymbol == "unknown"
            and edge.confidence == "unresolved"
            for edge in payload["connection_rows"]
        ))

    def test_javascript_chunks_capture_classes_functions_and_import_calls(self):
        payload = build_extraction_payload(
            "repo-3",
            [
                {
                    "path": "lib/helper.js",
                    "content": "export function helper() {\n  return true;\n}\n",
                },
                {
                    "path": "lib/controller.js",
                    "content": (
                        "import { helper } from './helper';\n\n"
                        "export class Controller {\n"
                        "  run() {\n"
                        "    helper();\n"
                        "    missing();\n"
                        "  }\n"
                        "}\n\n"
                        "export const makeController = () => new Controller();\n"
                    ),
                },
            ],
        )

        chunks = _by_full_name(payload["chunk_rows"])
        controller = chunks["lib.controller.Controller"]
        run = chunks["lib.controller.Controller.run"]
        chunks["lib.helper.helper"]

        self.assertEqual(controller.metadataJson["language"], "javascript")
        self.assertEqual(controller.metadataJson["semanticKind"], "class")
        self.assertIn("lib.controller.Controller", controller.metadataJson["exports"])
        self.assertEqual(run.parentChunkId, controller.id)
        self.assertTrue(run.content.strip().startswith("run()"))

        import_edges = [edge for edge in payload["connection_rows"] if edge.connectionType == "import"]
        call_edges = [edge for edge in payload["connection_rows"] if edge.connectionType == "call"]
        self.assertTrue(any(
            edge.targetSymbol == "./helper.helper"
            and edge.targetPath == "lib/helper.js"
            and edge.confidence == "resolved"
            for edge in import_edges
        ))
        self.assertTrue(any(
            edge.targetSymbol == "helper"
            and edge.targetPath == "lib/helper.js"
            and edge.confidence == "resolved"
            for edge in call_edges
        ))
        self.assertTrue(any(
            edge.targetSymbol == "missing"
            and edge.targetChunkId is None
            and edge.confidence == "unresolved"
            for edge in call_edges
        ))


if __name__ == "__main__":
    unittest.main()
