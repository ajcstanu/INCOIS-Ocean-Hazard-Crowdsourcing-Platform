
Claude finished the response
You said: About INCOISThe Indian National Centre for Ocean Information Services (INCOIS), operating under the administrative control of the Ministry of Earth Sciences, p…
About INCOISThe Indian National Centre for Ocean Information Services (INCOIS), operating under the administrative control of the Ministry of Earth Sciences, provides ocean information and advisory services to support disaster risk reduction and ensure maritime safety for coastal stakeholders. Its early warning services cover hazards such as tsunamis, storm surges, high waves, swell surges, and coastal currents, enabling authorities and communities to make informed decisions during ocean-related emergencies.BackgroundIndia’s vast coastline is vulnerable to a range of ocean hazards such as tsunamis, storm surges, high waves, coastal currents, and abnormal sea behaviour. While agencies like INCOIS provide early warnings based on satellite data, sensors, and numerical models; real-time field reporting from citizens and local communities are often unavailable or delayed. Additionally, valuable insights from public discussions on social media during hazard events remain untapped, yet can be critical for understanding ground realities, public awareness, and the spread of information.Detailed DescriptionThere is a need for a unified platform that enables citizens, coastal residents, volunteers, and disaster managers to report observations during hazardous ocean events (e.g., unusual tides, flooding, coastal damage, tsunami, swell surges, high waves, etc.) and to monitor public communication trends via social media.This platform should:• Allow citizens to submit geotagged reports, photos, or videos of observed ocean hazards via a mobile/web app.• Support role-based access for citizens, officials, and analysts.• Aggregate and visualize real-time crowdsourced data on a dynamic dashboard.• Visualize all crowdsourced reports and social media indicators on an interactive map, with hotspots dynamically generated based on report density, keyword frequency, or verified incidents.• Integrate social media feeds (e.g., Twitter, public Facebook posts, YouTube comments) and apply Text Classification/Natural Language Processing to extract hazard-related discussions and trends.• Help emergency response agencies understand the scale, urgency, and sentiment of hazard events.• Provide filters by location, event type, date, and source, enabling better situational awareness and faster validation of warning models.Expected SolutionAn integrated software platform (mobile + web) with:• User registration and reporting interface with media upload.• Map-based dashboard showing live crowd reports and social media activity.• Dynamic hotspot generation based on report volume or verified threat indicators.• Backend database and API for data management and integration with early warning systems.• NLP engine for detecting relevant hazard-related posts, keywords, and engagement metrics.• Multilingual support for regional accessibility.• Offline data collection capabilities (sync later), useful for remote coastal areas.
github code i need

Show more
11:09 PM
Claude responded: This is a comprehensive platform.

Reading frontend design skill
Reading frontend design skill
This is a comprehensive platform. I'll build you a complete GitHub-ready codebase with a well-structured project. Let me create the full stack solution.


Created 7 files, ran a command
Created 7 files, ran a command

Create project structure
bash

mkdir -p /home/claude/incois-platform/{backend/{src/{models,routes,middleware,services,utils},config},frontend/{public,src/{components/{Map,Dashboard,Reports,Auth,Admin},pages,hooks,utils,services,context}},mobile/src,docs} && echo "done"
Output

done

Root README
README.md

Backend package.json
package.json

Backend .env.example
.env.example

Main Express server entry point
index.js

Database config
database.js

Redis config
redis.js

User model
User.js
Done

You are out of free messages until 3:50 AM



Claude is AI and can make mistakes. Please double-check responses.
Index · JS
