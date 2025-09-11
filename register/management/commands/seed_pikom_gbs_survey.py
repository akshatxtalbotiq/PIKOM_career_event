from django.core.management.base import BaseCommand
from register.models import Survey, Question


class Command(BaseCommand):
    help = "Seed the PIKOM Talent Gap & Digital Workforce Survey 2025"

    def handle(self, *args, **kwargs):
        title = "PIKOM Talent Gap & Digital Workforce Survey 2025"
        survey, _ = Survey.objects.get_or_create(title=title)

        def q(num, text, qtype, choices=None, allow_other=False, max_checks=None, help_text="", required=True):
            Question.objects.update_or_create(
                survey=survey, number=num,
                defaults=dict(
                    text=text,
                    question_type=qtype,
                    choices=choices or None,
                    allow_other=allow_other,
                    max_checks=max_checks,
                    help_text=help_text,
                    is_required=required
                )
            )

        # --- GBS ---
        q(21, "Skills Demand vs Availability.<br />Which of the following skills specific to the GBS industry are most critical for your operations but are currently difficult to source locally? (Select up to 3)", "checkbox",
          [
            "Multilingual and cross-cultural communication skills",
            "Domain expertise (finance, HR, IT, procurement, supply chain)",
            "Digital/tech capabilities (AI, RPA, data analytics, cybersecurity, cloud)",
            "Customer experience and service management",
            "Leadership & people management in a shared services environment",
            "Problem-solving & process improvement (Lean, Six Sigma, Design Thinking)",          
          ],
          allow_other=True, max_checks=3, required=True)
        
        q(22, "Workforce Readiness.<br />To what extent do you feel Malaysia’s current talent pipeline (fresh graduates and early-career professionals) is ready to support the evolving needs of the GBS industry?", "radio",
          [
            "Very well prepared",
            "Somewhat prepared",
            "Neutral",
            "Somewhat unprepared",
            "Not prepared at all",
          ], required=True)

        q(23, "Retention & Attrition Challenges.<br />What are the top challenges your GBS organization faces in retaining talent? (Select up to 3)", "checkbox",
          [
            "Competitive salary and benefits offered by other employers",
            "Limited career pathways within GBS organizations",
            "Skills mismatch for digital/automation-enabled roles",
            "Demand for regional/global mobility opportunities",
            "Employee engagement & workplace culture issues",
            "High industry-wide competition for niche skills",         
          ],
          allow_other=True, max_checks=3, required=True)
        
        q(24, "Future Skills for GBS.<br />Which skill areas will be most important for the GBS industry in Malaysia over the next 3-5 years? (Select all that apply)", "checkbox",
          [
            "Advanced automation & AI integration",
            "Data analytics & business insights for decision-making",
            "Cybersecurity & data governance",
            "Cloud, digital platforms & infrastructure management",
            "Customer experience & service excellence",
            "ESG, compliance & sustainability knowledge",
            "Domain-specific expertise (finance, HR, procurement, IT, etc.)", 
          ],
          allow_other=True, required=True)
        
        q(25, "Ecosystem & Policy Support.<br />What changes or support (from government, academia, or industry associations) would most effectively help close the GBS talent gaps in Malaysia? ", "textarea", required=False)

        

        self.stdout.write(self.style.SUCCESS(f"Seeded survey: {title}"))
