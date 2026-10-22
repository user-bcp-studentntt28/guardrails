"""Contract checks for the architect prompt without calling an LLM."""

import unittest

from agents.architect import architect_node


class ArchitectTests(unittest.TestCase):
    def test_prompt_preserves_context_and_structured_deliverables(self):
        prompts = []
        report = "## Analysis\nDiagnóstico pendiente.\n## Plan\nPlan bloqueado."

        def invoke(prompt):
            prompts.append(prompt)
            return report

        result = architect_node(
            {
                "repo_name": "team/product",
                "project_type": "backend",
                "context": "Issue #12: conservar el contrato de consulta.",
                "snapshot": "### app/api.py\nCONTRACT_MARKER",
            },
            invoke,
        )

        self.assertEqual(len(prompts), 1)
        prompt = prompts[0]
        for expected in (
            "Eres el arquitecto de software del equipo",
            "Issue #12: conservar el contrato de consulta.",
            "Repositorio: team/product",
            "Tipo: backend",
            "CONTRACT_MARKER",
            "### 3. Componentes, responsabilidades y límites",
            "### 4. Contratos de API e interfaces",
            "### 6. Trazabilidad de aceptación",
            "### 7. Supuestos y preguntas pendientes",
            "### 8. Diseño técnico entregable",
            "### 2. Archivos y secuencia de cambios",
            "NO DISPONIBLE",
            "BLOQUEADO",
            "NO EJECUTADA",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, prompt)
        self.assertEqual(
            result,
            {
                "out_architect": report,
                "out_analysis": "Diagnóstico pendiente.",
                "out_plan": "Plan bloqueado.",
            },
        )

    def test_minimal_state_keeps_default_project_type(self):
        def invoke(prompt):
            self.assertIn("Tipo: ambos", prompt)
            return "## Analysis\nSin contexto.\n## Plan\nPedir evidencia."

        result = architect_node(
            {"repo_name": "team/product", "snapshot": ""},
            invoke,
        )
        self.assertEqual(result["out_plan"], "Pedir evidencia.")

    def test_design_is_a_deliverable_for_every_architecture_request(self):
        def invoke(prompt):
            for requirement in (
                "un diseño técnico nuevo o actualizado por cada solicitud",
                "Entrega el contenido del diseño en este informe",
                "solicitud | diseño D-n | criterios",
                "Criterio | comportamiento verificable | diseño D-n y vista",
                "tipo NUEVO o ACTUALIZACIÓN",
                "diagrama Mermaid de componentes y relaciones",
                "diagrama Mermaid de secuencia",
                "Delta actual a objetivo",
                "entrega igualmente el diseño actualizado",
                "diseño parcial identificado como BLOQUEADO",
                "no\nequivale a haber persistido o aprobado el documento",
                "con sus vistas y contratos, antes de la implementación dependiente",
            ):
                with self.subTest(requirement=requirement):
                    self.assertIn(requirement, prompt)
            return "## Analysis\nDiseño D-1 propuesto.\n## Plan\nVersionar D-1."

        result = architect_node(
            {"repo_name": "team/product", "snapshot": ""},
            invoke,
        )
        self.assertIn("Diseño D-1", result["out_analysis"])
        self.assertEqual(result["out_plan"], "Versionar D-1.")

    def test_invalid_output_still_fails_explicitly(self):
        for report in (
            "Sin secciones",
            "## Analysis\nDiagnóstico.",
            "## Analysis\nDiagnóstico.\n## Plan\n ",
            "Preámbulo\n## Analysis\nDiagnóstico.\n## Plan\nPlan.",
        ):
            with self.subTest(report=report):
                with self.assertRaisesRegex(ValueError, "## Analysis y ## Plan"):
                    architect_node(
                        {"repo_name": "team/product", "snapshot": ""},
                        lambda _: report,
                    )
