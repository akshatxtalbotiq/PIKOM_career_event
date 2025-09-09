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

        # --- Section A ---
        q(1, "What industry best describes your company?", "select",
          [
            "Information Technology (IT) / Software",
            "Financial Services",
            "Manufacturing",
            "E-commerce & Retail",
            "Professional Services (Consulting, BPO, etc.)",
            "Healthcare",
            "Logistics",
            "Public Sector",
            "Other",
          ],
          allow_other=True, required=True)

        q(2, "What is the size of your organization in Malaysia?", "select",
          ["1-10 employees", "11-50 employees", "51-250 employees", "250 - 1000 employees", "> 1000 employees"],required=True)

        q(3, "What is your primary role in the company?", "select",
          ["C-Suite (CEO, CIO, CTO, etc.)", "HR Director / Manager", "Department Head / Team Lead", "Founder / Co-founder / Owner", "Other"],
          allow_other=True, required=True)

        q(4, "Location (State)", "text", required=True)

        # --- Section B ---
        q(5, "Over the last 12 months, how challenging has it been to fill your open digital/tech positions?", "radio",
          [
            "1 - Not at all challenging",
            "2 - Slightly challenging",
            "3 - Moderately challenging",
            "4 - Very challenging",
            "5 - Extremely challenging",
          ], required=True)

        # --- Section C ---
        q(6, "Please indicate your company's demand for the following roles in upcoming 12 months.", "matrix_roles", required=True)

        q(7, "From the list below, select the TOP 5 most critical technical skills your company is looking for right now.", "checkbox",
          [
            "Cloud (AWS, Azure, GCP)",
            "AI / Machine Learning (TensorFlow, PyTorch)",
            "Generative AI & LLMs",
            "Data Analytics & Visualization (Power BI, Tableau)",
            "Backend Programming (Python, Java, Node.js)",
            "Frontend Programming (React, Angular, Vue.js)",
            "Cybersecurity (Threat Detection, Pen Testing)",
            "DevOps & CI/CD Tools",            
          ],
          allow_other=True, max_checks=5, required=True)

        q(8, "Top Three Most Difficult Skills to Hire (select up to 3)", "checkbox",
          [
            "Artificial Intelligence / Machine Learning",
            "Data Science / Analytics",
            "Cloud Computing",
            "Cybersecurity",
            "DevOps",
            "Software Development",
            "UI/UX Design",
            "Digital Marketing",
            "IoT",
            "Blockchain",
            "Robotics",           
          ],
          allow_other=True, max_checks=3, required=True)

        # --- Section D ---
        q(9, "What are the primary barriers you face when hiring local digital talent? (Select up to 3)", "checkbox",
          [
            "High salary expectations of candidates",
            "Lack of relevant technical skills",
            "Insufficient practical experience",
            "Cultural fit / Soft skills mismatch",
            "Limited awareness of emerging technologies",
            "Competition from multinational companies",           
          ],
          allow_other=True, max_checks=3, required=True)

        q(10, "Does your company have a training budget for digital/AI skills?", "select",
          ["Yes, Dedicated", "Yes, General", "No, but planning", "No"], required=True)

        q(11, "Methods used for employee upskilling (Select all that apply)", "checkbox",
          ["Internal training", "Online courses", "External providers", "On-the-job learning"], required=True)

        q(12, "Main barriers to effective training:", "checkbox",
          ["Cost", "Time constraints", "Employee resistance", "Program quality", "Other"],
          allow_other=True, required=True)

        q(13, "Preferred Candidate Type (Select all that apply):", "checkbox",
          ["Full-Time", "Contract", "Internship"], required=True)

        # --- Section E ---
        q(14, "Voluntary attrition rate for digital/AI roles last year:", "select",
          ["<5%", "5–10%", "11-20%", ">20%", "Don’t track"], required=True)

        q(15, "Top reasons employees leave (select up to 2):", "checkbox",
          [
            "Better salary elsewhere",
            "Limited career growth",
            "Burnout/workload",
            "Desire for remote work",
            "Cultural misalignment",
            "Relocation abroad",
            "Personal/family reasons",           
          ],
          allow_other=True, max_checks=2, required=True)

        # --- Section F ---
        q(16, "Does your company offer internships in digital/AI fields?", "select",
          ["Yes, regularly", "Yes, occasionally", "No, planning to", "No"], required=True)

        q(17, "Roles interns support:", "checkbox",
          ["Development", "Data/reporting", "Digital marketing", "UI/UX", "Business ops", "Research", "Customer support", "Automation"],
          allow_other=True, required=True)

        # --- Section G ---
        q(18, "Looking ahead 2-3 years, which emerging technology area will be most critical for your company's growth? (Select one)", "radio",
          [
            "Artificial Intelligence / Machine Learning",
            "Generative AI",
            "Applied AI & Automation",
            "Green Tech / Sustainability Tech",
            "Web3 / Blockchain",
            "Advanced Cybersecurity (e.g., Zero Trust)",          
          ],
          allow_other=True, required=True)

        q(19, "What type of support or government initiatives would provide the most significant help? (Select up to 2)", "checkbox",
          [
            "Subsidies/grants for hiring and training fresh graduates",
            "Incentives for upskilling/reskilling existing employees",
            "Streamlining employment pass processes for foreign tech talent",
            "Industry-academia collaboration projects",
            "Tax incentives for companies investing in R&D and high-tech roles",
          ],
          max_checks=2, required=True)

        q(20, "Do you have any other comments or suggestions?", "textarea", required=False)

        self.stdout.write(self.style.SUCCESS(f"Seeded survey: {title}"))
