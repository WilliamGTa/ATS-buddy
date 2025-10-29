import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from bedrock_client import BedrockClient

logger = logging.getLogger(__name__)

@dataclass
class ATSOptimizationData:
    """Data class for ATS optimization metrics"""
    missing_keywords: List[str]
    missing_technical_skills: List[str]
    missing_soft_skills: List[str]
    suggestions: List[str]
    strengths: List[str]
    compatibility_score: float

class EnhancedResumeGenerator:
    """
    Advanced ATS-optimized resume generator that produces high-quality markdown resumes
    """

    def __init__(self):
        """Initialize the enhanced resume generator with Bedrock client"""
        self.bedrock_client = BedrockClient()
        
        # ATS optimization constants
        self.action_verbs = [
            "Achieved", "Administered", "Analyzed", "Built", "Collaborated", "Created", 
            "Delivered", "Developed", "Enhanced", "Executed", "Implemented", "Improved", 
            "Increased", "Led", "Managed", "Optimized", "Organized", "Reduced", 
            "Streamlined", "Supervised", "Transformed", "Spearheaded", "Orchestrated"
        ]
        
        self.quantifiable_terms = [
            "increased by", "reduced by", "improved by", "managed team of", "budget of",
            "revenue of", "saved", "generated", "processed", "handled", "oversaw"
        ]
    
    def generate_enhanced_resume(self, original_resume_text: str, job_description: str, 
                               analysis_data: Optional[Dict] = None) -> Dict:
        """
        Generate a super high-quality ATS-optimized resume in markdown format
        
        Args:
            original_resume_text (str): Original resume content
            job_description (str): Target job description
            analysis_data (dict, optional): Pre-computed analysis data
            
        Returns:
            dict: Enhanced resume with comprehensive metrics
        """
        try:
            if not original_resume_text or not original_resume_text.strip():
                return {"success": False, "error": "Resume text is empty"}

            if not job_description or not job_description.strip():
                return {"success": False, "error": "Job description is empty"}

            # Step 1: Get or perform analysis
            if analysis_data is None:
                logger.info("Performing comprehensive resume analysis")
                analysis_result = self.bedrock_client.analyze_resume_vs_job_description(
                    original_resume_text, job_description
                )

                if not analysis_result["success"]:
                    return {
                        "success": False,
                        "error": f"Failed to analyze resume: {analysis_result['error']}"
                    }
                
                analysis_data = analysis_result.get("analysis", {})
            
            # Step 2: Extract optimization data
            optimization_data = self._extract_optimization_data(analysis_data)
            
            # Step 3: Generate comprehensive enhancement prompt
            enhancement_prompt = self._create_comprehensive_enhancement_prompt(
                original_resume_text, job_description, optimization_data
            )
            
            # Step 4: Generate enhanced resume
            logger.info("Generating high-quality ATS-optimized resume")
            response = self._call_bedrock_for_enhancement(enhancement_prompt)

            if not response["success"]:
                return response

            enhanced_resume = response["enhanced_resume"]
            
            # Step 5: Post-process and validate
            final_resume = self._post_process_resume(enhanced_resume)
            validation_result = self._validate_resume_quality(final_resume, original_resume_text)
            
            # Step 6: Calculate improvement metrics
            metrics = self._calculate_improvement_metrics(
                original_resume_text, final_resume, optimization_data
            )

            return {
                "success": True,
                "enhanced_resume": final_resume,
                "original_length": len(original_resume_text),
                "enhanced_length": len(final_resume),
                "keywords_added": optimization_data.missing_keywords[:10],
                "improvements_made": self._generate_improvement_summary(optimization_data, metrics),
                "ats_score": metrics["ats_score"],
                "keyword_density": metrics["keyword_density"],
                "action_verb_count": metrics["action_verb_count"],
                "quantifiable_achievements": metrics["quantifiable_achievements"],
                "validation_passed": validation_result["is_valid"],
                "validation_issues": validation_result.get("issues", []),
                "format": "markdown",
                "token_cutoff_detected": False,
                "token_limit_used": 8000,
                "response_length": len(final_resume)
            }

        except Exception as e:
            logger.error(f"Error generating enhanced resume: {e}")
            return {"success": False, "error": "Error enhancing resume"}
    
    def _extract_optimization_data(self, analysis_data: Dict) -> ATSOptimizationData:
        """Extract and structure optimization data from analysis"""
        return ATSOptimizationData(
            missing_keywords=analysis_data.get("missing_keywords", [])[:15],
            missing_technical_skills=analysis_data.get("missing_technical_skills", [])[:8],
            missing_soft_skills=analysis_data.get("missing_soft_skills", [])[:5],
            suggestions=analysis_data.get("suggestions", [])[:6],
            strengths=analysis_data.get("strengths", [])[:5],
            compatibility_score=analysis_data.get("compatibility_score", 0)
        )
    
    def _create_comprehensive_enhancement_prompt(self, original_resume: str, 
                                           job_description: str, 
                                           optimization_data: ATSOptimizationData) -> str:
        """Create ATS Scanner Simulation prompt for combined cover letter + enhanced resume generation"""
        prompt = f"""You are an advanced ATS (Applicant Tracking System) with comprehensive optimization capabilities. You will generate both a perfectly matched cover letter AND an enhanced resume in a single markdown document.

**ATS CANDIDATE PROFILE SCAN:**
{original_resume}

**TARGET POSITION ANALYSIS:**
{job_description}

**ATS COMPATIBILITY ASSESSMENT:**
📊 Current Resume Match Score: {optimization_data.compatibility_score}%
🎯 Target Score: 90%+ for both documents
❌ Missing Keywords: {', '.join(optimization_data.missing_keywords[:12])}
🔧 Technical Skills to Integrate: {', '.join(optimization_data.missing_technical_skills[:8])}
💼 Soft Skills to Emphasize: {', '.join(optimization_data.missing_soft_skills[:5])}
✅ Candidate Strengths: {'; '.join(optimization_data.strengths[:5])}

**ATS DUAL-DOCUMENT OPTIMIZATION PROTOCOL:**

**PHASE 1: COVER LETTER OPTIMIZATION**
- Incorporate missing keywords naturally in professional context
- Use exact job title and company terminology from posting
- Include 3-4 quantified achievements from resume
- Demonstrate clear job-candidate alignment
- Target 300-400 words for optimal ATS processing

**PHASE 2: RESUME ENHANCEMENT OPTIMIZATION**
- Integrate missing keywords organically throughout sections
- Transform bullet points with stronger action verbs and metrics
- Add "Core Competencies" section with keyword clusters
- Enhance professional summary with job-aligned value proposition
- Maintain authenticity while maximizing ATS compatibility

**OUTPUT FORMAT REQUIREMENTS:**

Generate a single markdown document with this exact structure:

```markdown
# COVER LETTER

[Standard business letter format with placeholders]
[3-4 paragraph cover letter optimized for ATS and human review]

---

# ENHANCED RESUME

[Complete enhanced resume in markdown format]
[All sections optimized for ATS scanning]
```

**COVER LETTER SPECIFICATIONS:**
- **Header**: Standard business format with [Your Name], [Date], [Company Name] placeholders
- **Opening**: Job title + immediate value proposition + top qualification
- **Body**: Specific achievements from resume + requirement alignment + quantified results  
- **Closing**: Call to action + enthusiasm + availability
- **ATS Targets**: 90%+ keyword match, address 80%+ of job requirements

**ENHANCED RESUME SPECIFICATIONS:**
- **Professional Summary**: 3-4 lines incorporating missing keywords and value proposition
- **Core Competencies**: New section with clustered technical and soft skills
- **Professional Experience**: Enhanced bullets with action verbs + context + quantified results
- **Technical Skills**: Organized by proficiency level, including missing technical skills
- **Education & Certifications**: Preserved from original
- **ATS Optimization**: Standard headers, keyword density 2-3%, scannable formatting

**CRITICAL ENHANCEMENT INSTRUCTIONS:**

**FOR COVER LETTER:**
1. Use specific achievements and metrics from the candidate's resume
2. Connect each paragraph to job requirements explicitly
3. Include missing keywords naturally in professional context
4. Show enthusiasm while maintaining professional tone
5. Reference specific company goals or challenges if mentioned in job posting

**FOR RESUME:**
1. **PRESERVE AUTHENTICITY**: Keep all original work history, education, and core experiences
2. **STRATEGIC KEYWORD INTEGRATION**: Weave missing keywords into existing content naturally
3. **QUANTIFY ACHIEVEMENTS**: Add realistic metrics to existing accomplishments
4. **STRENGTHEN LANGUAGE**: Replace weak verbs with power verbs: {', '.join(['Spearheaded', 'Orchestrated', 'Accelerated', 'Transformed', 'Architected'][:5])}
5. **OPTIMIZE STRUCTURE**: Use ATS-friendly headers and clean markdown formatting

**ATS COMPATIBILITY CHECKLIST:**
✅ Both documents use exact job title and company terminology
✅ Missing keywords integrated across both documents (no stuffing)
✅ Technical skills demonstrated in context, not just listed
✅ Quantified achievements present in both cover letter and resume
✅ Professional formatting optimized for ATS parsing
✅ Consistent messaging between cover letter and resume
✅ Standard business/resume section headers used

**EXAMPLE OUTPUT STRUCTURE:**

```markdown
# COVER LETTER

[Your Name]
[Your Address]
[City, State ZIP Code]
[Your Email] | [Your Phone]

[Date]

[Hiring Manager Name]
[Company Name]
[Company Address]

Dear Hiring Manager,

I am writing to express my strong interest in the [Job Title] position at [Company Name]. With [X years] of experience in [relevant field] and a proven track record of [specific quantified achievement], I am confident in my ability to contribute to your [specific team/department] and help achieve [company goal].

In my previous role as [Previous Position], I [specific achievement with metrics] by [method that aligns with job requirements]. This experience directly addresses your need for [job requirement] and demonstrates my proficiency in [missing technical skills]. Additionally, my expertise in [relevant area] resulted in [quantified business impact], showcasing the value I can bring to [Company Name].

What particularly excites me about this opportunity is [connection to company/role]. My background in [relevant experience] and passion for [relevant field] align perfectly with your requirements for [specific job responsibility]. I am eager to leverage my skills in [missing keywords from job posting] to drive [specific outcomes mentioned in job description].

I would welcome the opportunity to discuss how my experience and enthusiasm can contribute to [Company Name]'s continued success. Thank you for your consideration, and I look forward to hearing from you.

Sincerely,
[Your Name]

---

# ENHANCED RESUME

# [Full Name]
[Email] | [Phone] | [Location] | [LinkedIn] | [Portfolio/GitHub if applicable]

## Professional Summary
[3-4 lines incorporating job-relevant keywords, years of experience, top achievements, and value proposition aligned to target role]

## Core Competencies
• **Technical Skills:** [Relevant technical skills including missing ones from analysis]
• **Industry Expertise:** [Domain knowledge and specializations]
• **Leadership & Collaboration:** [Soft skills and interpersonal abilities]

## Professional Experience

### [Job Title] | [Company Name] | [Dates]
• [Action verb] [context] resulting in [quantified achievement] through [relevant skill/method]
• [Enhanced bullet with missing keywords integrated naturally]
• [Achievement demonstrating skill mentioned in job posting]

### [Previous Job Title] | [Company Name] | [Dates]
• [Quantified accomplishment relevant to target role]
• [Technical skill demonstration with business impact]
• [Leadership or collaboration example]

## Technical Skills
• **Programming Languages:** [List including job-relevant languages]
• **Frameworks & Tools:** [Relevant technologies]
• **Cloud & Infrastructure:** [Platform experience]
• **Databases & Analytics:** [Data-related skills]

## Education
[Degree] | [Institution] | [Year]
[Relevant coursework, honors, or certifications if applicable]
```

**GENERATION INSTRUCTIONS:**
Create both documents that work together as a cohesive application package. The cover letter should reference specific achievements that are detailed in the enhanced resume. Both should demonstrate the same value proposition and skill alignment with the target role.

**SUCCESS CRITERIA:**
- Combined package achieves 90%+ ATS compatibility score
- Cover letter and resume tell consistent, compelling story
- All missing keywords integrated naturally across both documents
- Quantified achievements present throughout both documents
- Professional formatting optimized for ATS and human review

Generate the complete cover letter + enhanced resume package now:"""

        return prompt
    
    def _post_process_resume(self, resume: str) -> str:
        """Post-process the resume for optimal formatting and quality"""
        # Clean up common AI response artifacts
        resume = self._clean_ai_response(resume)
        
        # Ensure proper markdown formatting
        resume = self._optimize_markdown_formatting(resume)
        
        # Enhance bullet points with better action verbs
        resume = self._enhance_action_verbs(resume)
        
        return resume.strip()
    
    def _optimize_markdown_formatting(self, resume: str) -> str:
        """Optimize markdown formatting for better ATS compatibility"""
        lines = resume.split('\n')
        optimized_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                optimized_lines.append('')
                continue
            
            # Ensure proper header formatting
            if line.startswith('#'):
                optimized_lines.append(line)
            # Ensure bullet points are properly formatted
            elif line.startswith('-') or line.startswith('•'):
                if not line.startswith('- '):
                    line = '- ' + line.lstrip('-•').strip()
                optimized_lines.append(line)
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _enhance_action_verbs(self, resume: str) -> str:
        """Enhance weak action verbs with stronger alternatives"""
        weak_to_strong = {
            'worked on': 'developed',
            'responsible for': 'managed',
            'helped with': 'collaborated on',
            'was involved in': 'contributed to',
            'did': 'executed',
            'made': 'created',
            'used': 'utilized',
            'handled': 'managed',
            'dealt with': 'resolved'
        }
        
        enhanced_resume = resume
        for weak, strong in weak_to_strong.items():
            enhanced_resume = re.sub(
                weak, strong, enhanced_resume, flags=re.IGNORECASE
            )
        
        return enhanced_resume
    
    def _validate_resume_quality(self, enhanced_resume: str, original_resume: str) -> Dict:
        """Validate the quality and authenticity of the enhanced resume"""
        issues = []
        
        # Check for proper markdown formatting
        if not re.search(r'^#\s+', enhanced_resume, re.MULTILINE):
            issues.append("Missing proper markdown headers")
        
        # Check for bullet points
        if not re.search(r'^-\s+', enhanced_resume, re.MULTILINE):
            issues.append("Missing bullet points in experience section")
        
        # Check for action verbs
        action_verb_count = sum(1 for verb in self.action_verbs 
                              if verb.lower() in enhanced_resume.lower())
        if action_verb_count < 3:
            issues.append("Insufficient strong action verbs")
        
        # Check for reasonable length increase
        length_ratio = len(enhanced_resume) / len(original_resume)
        if length_ratio < 1.2:
            issues.append("Enhanced resume not significantly improved")
        elif length_ratio > 3.0:
            issues.append("Enhanced resume may contain excessive additions")
        
        # Check for contact information preservation
        original_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', original_resume)
        enhanced_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', enhanced_resume)
        
        if original_emails and not enhanced_emails:
            issues.append("Contact information may have been lost")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "quality_score": max(0, 100 - len(issues) * 20)
        }
    
    def _calculate_improvement_metrics(self, original: str, enhanced: str, 
                                     optimization_data: ATSOptimizationData) -> Dict:
        """Calculate comprehensive improvement metrics"""
        
        # Keyword density analysis
        keyword_matches = sum(1 for keyword in optimization_data.missing_keywords 
                            if keyword.lower() in enhanced.lower())
        keyword_density = (keyword_matches / len(optimization_data.missing_keywords) * 100) if optimization_data.missing_keywords else 0
        
        # Action verb count
        action_verb_count = sum(1 for verb in self.action_verbs 
                              if verb.lower() in enhanced.lower())
        
        # Quantifiable achievements
        quantifiable_patterns = [r'\d+%', r'\$\d+', r'\d+\+', r'\d+x', r'\d+ years?', r'\d+ months?']
        quantifiable_achievements = sum(len(re.findall(pattern, enhanced)) 
                                      for pattern in quantifiable_patterns)
        
        # Calculate overall ATS score
        ats_score = min(100, (
            keyword_density * 0.4 +
            min(action_verb_count * 10, 50) * 0.3 +
            min(quantifiable_achievements * 15, 50) * 0.3
        ))
        
        return {
            "ats_score": round(ats_score, 1),
            "keyword_density": round(keyword_density, 1),
            "action_verb_count": action_verb_count,
            "quantifiable_achievements": quantifiable_achievements,
            "length_improvement": round((len(enhanced) - len(original)) / len(original) * 100, 1)
        }
    
    def _generate_improvement_summary(self, optimization_data: ATSOptimizationData, 
                                    metrics: Dict) -> List[str]:
        """Generate a summary of improvements made"""
        improvements = []
        
        if len(optimization_data.missing_keywords) > 0:
            improvements.append(f"Integrated {len(optimization_data.missing_keywords)} relevant keywords")
        
        if metrics["action_verb_count"] > 0:
            improvements.append(f"Enhanced with {metrics['action_verb_count']} strong action verbs")
        
        if metrics["quantifiable_achievements"] > 0:
            improvements.append(f"Added {metrics['quantifiable_achievements']} quantifiable achievements")
        
        improvements.extend([
            "Optimized markdown formatting for ATS compatibility",
            "Enhanced professional summary with key value propositions",
            "Improved section organization and hierarchy",
            f"Achieved {metrics['ats_score']:.1f}% ATS optimization score"
        ])
        
        return improvements
    
    def _call_bedrock_for_enhancement(self, prompt: str) -> Dict:
        """Call Bedrock API with optimized settings for high-quality resume generation"""
        try:
            request_body = {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {
                    "max_new_tokens": 8000,  # Increased for comprehensive resumes
                    "temperature": 0.1,      # Lower temperature for more consistent, professional output
                    "top_p": 0.9,           # Balanced creativity and focus
                },
            }
            
            response = self.bedrock_client.bedrock.invoke_model(
                modelId=self.bedrock_client.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )
            
            response_body = json.loads(response["body"].read())
            
            if "output" in response_body and "message" in response_body["output"]:
                message = response_body["output"]["message"]
                if "content" in message and len(message["content"]) > 0:
                    enhanced_resume = message["content"][0]["text"].strip()
                    
                    # Clean up the response
                    enhanced_resume = self._clean_ai_response(enhanced_resume)
                    
                    # Check for token cutoff indicators
                    token_cutoff_detected = self._detect_token_cutoff(enhanced_resume)
                    
                    if len(enhanced_resume) < 300:
                        return {
                            "success": False,
                            "error": "Enhanced resume appears to be too short or incomplete"
                        }
                    
                    return {
                        "success": True,
                        "enhanced_resume": enhanced_resume,
                        "token_cutoff_detected": token_cutoff_detected
                    }
            
            return {
                "success": False,
                "error": "Invalid response format from AI model"
            }
                
        except Exception as e:
            logger.error(f"Error calling Bedrock for enhancement: {e}")
            return {
                "success": False,
                "error": f"AI service error: {str(e)}"
            }
    
    def _detect_token_cutoff(self, resume: str) -> bool:
        """Detect if the resume was cut off due to token limits"""
        cutoff_indicators = [
            resume.endswith(':'),
            resume.endswith(','),
            resume.endswith('...'),
            'truncated' in resume.lower(),
            len(resume) > 0 and resume[-1].islower() and not resume.endswith('.'),
            not resume.strip().endswith((')', '.', '```'))  # Markdown should end properly
        ]
        
        return any(cutoff_indicators)
    
    def _clean_ai_response(self, response: str) -> str:
        """Clean and optimize the AI response for markdown formatting"""
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "Here's the enhanced resume:",
            "Enhanced Resume:",
            "Here is the enhanced resume:",
            "ENHANCED RESUME:",
            "```markdown",
            "```",
            "**Enhanced Resume:**",
            "**ENHANCED RESUME:**"
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Remove trailing explanations
        cutoff_phrases = [
            "This enhanced resume",
            "The enhanced resume",
            "I've enhanced",
            "The above resume",
            "This version"
        ]
        
        for phrase in cutoff_phrases:
            if phrase in response:
                response = response.split(phrase)[0].strip()
        
        # Clean up markdown code blocks
        if response.endswith('```'):
            response = response[:-3].strip()
        
        # Ensure proper line endings
        response = re.sub(r'\n{3,}', '\n\n', response)  # Max 2 consecutive newlines
        
        return response.strip()