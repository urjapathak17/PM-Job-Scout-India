# FILE 1: scripts/job_search.py
# Copy everything below this line for your first file

import os
import json
import requests
from datetime import datetime
from groq import Groq
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobSearchAutomation:
    def __init__(self):
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Boolean search query targeting ATS sites
        self.search_query = """
        (site:myworkdayjobs.com OR site:greenhouse.io OR site:lever.co OR 
         site:icims.com OR site:smartrecruiters.com OR site:taleo.net OR 
         site:jobvite.com OR site:workforcenow.adp.com OR site:bamboohr.com OR 
         site:brassring.com OR site:breezy.hr OR site:bullhorn.com OR 
         site:jazzhr.com OR site:jobdiva.com OR site:successfactors.com)
        ("product manager" OR "senior product manager" OR "associate product manager" OR "principal product manager")
        (India OR Bengaluru OR Bangalore OR Mumbai OR Delhi OR Gurgaon OR Gurugram OR Hyderabad OR Pune OR Chennai OR Noida OR Kolkata OR "New Delhi")
        """.replace('\n', ' ').strip()
    
    def search_jobs(self):
        """Search for jobs using SerpAPI"""
        try:
            url = "https://serpapi.com/search"
            params = {
                'engine': 'google',
                'q': self.search_query,
                'api_key': self.serpapi_key,
                'num': 50,
                'gl': 'in',
                'hl': 'en',
                'tbs': 'qdr:d'  # Last 24 hours only
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"SerpAPI returned {len(data.get('organic_results', []))} results")
            return data
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return None
    
    def process_with_ai(self, search_results):
        """Process search results with Groq AI"""
        try:
            if not search_results or 'organic_results' not in search_results:
                logger.warning("No search results to process")
                return []
            
            results = search_results['organic_results'][:30]  # Process top 30
            
            prompt = f"""
Analyze these Google search results for Product Manager jobs in India from ATS career sites.

SEARCH RESULTS:
{json.dumps(results, indent=2)[:4000]}  

TASK: Extract only legitimate Product Manager positions and return as JSON array.

RULES:
1. Only include roles with "Product Manager" in title (exclude Sales PM, Technical PM unless clearly product roles)
2. Must be from India or major Indian cities
3. Must be from career/ATS sites (not job boards like Naukri, Indeed)
4. Remove duplicates based on company + title
5. Exclude internships, contractor roles, and clearly irrelevant positions

REQUIRED JSON FORMAT:
[
  {{
    "title": "exact job title from listing",
    "company": "company name",
    "location": "city, state",
    "link": "complete URL",
    "snippet": "brief role description (1-2 lines)",
    "date_found": "{datetime.now().strftime('%Y-%m-%d')}"
  }}
]

Return ONLY valid JSON array, no additional text or markdown.
"""
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a job search expert. Always return valid JSON arrays only. Be strict about Product Manager roles."
                    },
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-70b-versatile",
                temperature=0.1,
                max_tokens=3000
            )
            
            ai_response = chat_completion.choices[0].message.content.strip()
            
            # Clean response to extract JSON
            if '```json' in ai_response:
                ai_response = ai_response.split('```json')[1].split('```')[0].strip()
            elif '```' in ai_response:
                ai_response = ai_response.split('```')[1].strip()
            
            # Parse JSON
            jobs = json.loads(ai_response)
            
            # Validate jobs format
            validated_jobs = []
            for job in jobs:
                if isinstance(job, dict) and all(key in job for key in ['title', 'company', 'link']):
                    # Add missing fields with defaults
                    job.setdefault('location', 'India')
                    job.setdefault('snippet', 'No description available')
                    job.setdefault('date_found', datetime.now().strftime('%Y-%m-%d'))
                    validated_jobs.append(job)
            
            logger.info(f"AI processed {len(validated_jobs)} valid jobs from {len(results)} search results")
            return validated_jobs
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response: {ai_response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error processing with AI: {e}")
            return []
    
    def send_telegram_alert(self, jobs):
        """Send job alerts to Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("Telegram credentials missing, skipping notification")
            return
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            if not jobs:
                message = """🔍 *Daily Job Search Complete*

No new Product Manager positions found today from ATS sites.

The automation searched through:
• Workday, Greenhouse, Lever
• ICIMS, SmartRecruiters, Taleo  
• BambooHR, Breezy, JazzHR
• And 6+ more ATS platforms

Try again tomorrow! 🚀

#JobSearch #ProductManager #India"""
            else:
                repo = os.getenv('GITHUB_REPOSITORY', 'username/repo')
                dashboard_url = f"https://{repo.replace('/', '.github.io/')}"
                
                message = f"🎯 *{len(jobs)} New Product Manager Jobs Found!*\n\n"
                
                # Show top 5 jobs
                for i, job in enumerate(jobs[:5], 1):
                    title = job.get('title', 'N/A')[:50]  # Truncate long titles
                    company = job.get('company', 'N/A')
                    location = job.get('location', 'N/A').split(',')[0]  # Just city
                    link = job.get('link', '#')
                    
                    message += f"{i}\\. *{title}*\n"
                    message += f"🏢 {company}\n"
                    message += f"📍 {location}\n"
                    message += f"🔗 [Apply Now]({link})\n\n"
                
                if len(jobs) > 5:
                    message += f"\\.\\.\\. and {len(jobs) - 5} more jobs\\!\n\n"
                
                message += f"📊 [View Full Dashboard]({dashboard_url})\n\n"
                message += "#ProductManager #Jobs #India #ATS"
            
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'MarkdownV2',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            logger.info("Telegram alert sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            # Try without markdown as fallback
            try:
                simple_message = f"🎯 Found {len(jobs)} new Product Manager jobs today! Check your dashboard for details."
                data = {
                    'chat_id': self.telegram_chat_id,
                    'text': simple_message
                }
                requests.post(url, json=data, timeout=30)
                logger.info("Sent simple Telegram fallback message")
            except:
                logger.error("Failed to send even simple Telegram message")
    
    def save_jobs_data(self, jobs):
        """Save jobs to JSON file and return new jobs only"""
        try:
            os.makedirs('data', exist_ok=True)
            jobs_file = 'data/jobs.json'
            
            # Load existing jobs
            existing_jobs = []
            if os.path.exists(jobs_file):
                with open(jobs_file, 'r') as f:
                    try:
                        existing_jobs = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning("Invalid existing jobs file, starting fresh")
                        existing_jobs = []
            
            # Simple deduplication by link
            existing_links = {job.get('link', '') for job in existing_jobs}
            new_jobs = [job for job in jobs if job.get('link', '') not in existing_links and job.get('link')]
            
            if new_jobs:
                # Add new jobs to the beginning
                all_jobs = new_jobs + existing_jobs
                # Keep only last 200 jobs to prevent file from growing too large
                all_jobs = all_jobs[:200]
                
                with open(jobs_file, 'w') as f:
                    json.dump(all_jobs, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved {len(new_jobs)} new jobs, total: {len(all_jobs)}")
                return new_jobs
            else:
                logger.info("No new jobs to save")
                return []
                
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")
            return []
    
    def run(self):
        """Main execution function"""
        logger.info("🚀 Starting daily job search automation")
        
        # Validate required environment variables
        required_vars = ['SERPAPI_KEY', 'GROQ_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return
        
        # Search for jobs
        logger.info("🔍 Searching for jobs...")
        search_results = self.search_jobs()
        
        if not search_results:
            logger.error("❌ No search results obtained")
            return
        
        # Process with AI
        logger.info("🧠 Processing results with AI...")
        processed_jobs = self.process_with_ai(search_results)
        
        # Save new jobs
        logger.info("💾 Saving job data...")
        new_jobs = self.save_jobs_data(processed_jobs)
        
        # Send notifications for new jobs only
        logger.info("📱 Sending notifications...")
        self.send_telegram_alert(new_jobs)
        
        # Log final summary
        logger.info(f"✅ Job search completed! Processed: {len(processed_jobs)}, New: {len(new_jobs)}")
        print(f"SUCCESS: Found {len(processed_jobs)} total jobs, {len(new_jobs)} are new")

if __name__ == "__main__":
    automation = JobSearchAutomation()
    automation.run()

# END OF FILE 1
