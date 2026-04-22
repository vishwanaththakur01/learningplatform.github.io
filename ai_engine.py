import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import json

class LearningPathwayAI:
    def __init__(self):
        self.learning_styles = ['visual', 'auditory', 'reading_writing', 'kinesthetic']
        self.difficulty_levels = ['beginner', 'intermediate', 'advanced']
        self.content_types = ['video', 'article', 'interactive', 'quiz', 'project']
        
        # Pre-trained model for learning style prediction
        self.style_model = self._initialize_style_model()
        
        # Course database (in production, this would be a database)
        self.course_database = self._initialize_course_database()
    
    def _initialize_style_model(self):
        """Initialize the learning style prediction model"""
        # In a real application, this would be trained on historical data
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        return model
    
    def _initialize_course_database(self):
        """Initialize sample course database"""
        return {
            'python': {
                'beginner': [
                    {'id': 'py-basics-1', 'title': 'Introduction to Python', 'type': 'video', 'duration': 15, 'difficulty': 'beginner'},
                    {'id': 'py-basics-2', 'title': 'Variables and Data Types', 'type': 'article', 'duration': 10, 'difficulty': 'beginner'},
                    {'id': 'py-basics-3', 'title': 'Basic Operators', 'type': 'interactive', 'duration': 20, 'difficulty': 'beginner'},
                    {'id': 'py-basics-4', 'title': 'Python Basics Quiz', 'type': 'quiz', 'duration': 15, 'difficulty': 'beginner'},
                ],
                'intermediate': [
                    {'id': 'py-int-1', 'title': 'Functions and Modules', 'type': 'video', 'duration': 25, 'difficulty': 'intermediate'},
                    {'id': 'py-int-2', 'title': 'Object-Oriented Programming', 'type': 'article', 'duration': 30, 'difficulty': 'intermediate'},
                    {'id': 'py-int-3', 'title': 'Error Handling', 'type': 'interactive', 'duration': 25, 'difficulty': 'intermediate'},
                    {'id': 'py-int-4', 'title': 'Mini Project: Calculator', 'type': 'project', 'duration': 60, 'difficulty': 'intermediate'},
                ],
                'advanced': [
                    {'id': 'py-adv-1', 'title': 'Decorators and Generators', 'type': 'video', 'duration': 35, 'difficulty': 'advanced'},
                    {'id': 'py-adv-2', 'title': 'Multithreading and Async', 'type': 'article', 'duration': 40, 'difficulty': 'advanced'},
                    {'id': 'py-adv-3', 'title': 'Advanced Patterns Project', 'type': 'project', 'duration': 120, 'difficulty': 'advanced'},
                ]
            },
            'web_development': {
                'beginner': [
                    {'id': 'web-basics-1', 'title': 'HTML Fundamentals', 'type': 'video', 'duration': 20, 'difficulty': 'beginner'},
                    {'id': 'web-basics-2', 'title': 'CSS Basics', 'type': 'interactive', 'duration': 30, 'difficulty': 'beginner'},
                    {'id': 'web-basics-3', 'title': 'Building Your First Webpage', 'type': 'project', 'duration': 45, 'difficulty': 'beginner'},
                ],
                'intermediate': [
                    {'id': 'web-int-1', 'title': 'JavaScript Fundamentals', 'type': 'video', 'duration': 35, 'difficulty': 'intermediate'},
                    {'id': 'web-int-2', 'title': 'DOM Manipulation', 'type': 'interactive', 'duration': 30, 'difficulty': 'intermediate'},
                    {'id': 'web-int-3', 'title': 'Responsive Design', 'type': 'article', 'duration': 25, 'difficulty': 'intermediate'},
                ]
            },
            'data_science': {
                'beginner': [
                    {'id': 'ds-basics-1', 'title': 'Introduction to Data Science', 'type': 'video', 'duration': 20, 'difficulty': 'beginner'},
                    {'id': 'ds-basics-2', 'title': 'Statistics Fundamentals', 'type': 'article', 'duration': 30, 'difficulty': 'beginner'},
                    {'id': 'ds-basics-3', 'title': 'Python for Data Science', 'type': 'interactive', 'duration': 45, 'difficulty': 'beginner'},
                ],
                'intermediate': [
                    {'id': 'ds-int-1', 'title': 'Machine Learning Basics', 'type': 'video', 'duration': 40, 'difficulty': 'intermediate'},
                    {'id': 'ds-int-2', 'title': 'Data Visualization', 'type': 'interactive', 'duration': 35, 'difficulty': 'intermediate'},
                    {'id': 'ds-int-3', 'title': 'Data Analysis Project', 'type': 'project', 'duration': 90, 'difficulty': 'intermediate'},
                ]
            }
        }
    
    def assess_learning_style(self, assessment_data):
        """
        Analyze assessment responses to determine learning style
        Returns the dominant learning style and confidence score
        """
        # Scoring system for different learning preferences
        scores = {
            'visual': 0,
            'auditory': 0,
            'reading_writing': 0,
            'kinesthetic': 0
        }
        
        # Process assessment responses
        for question, answer in assessment_data.items():
            if question in ['q1', 'q4', 'q7']:
                if answer in ['a', 'd']:
                    scores['visual'] += 1
                elif answer in ['b', 'c']:
                    scores['auditory'] += 1
            elif question in ['q2', 'q5', 'q8']:
                if answer in ['b', 'c']:
                    scores['reading_writing'] += 1
                elif answer in ['a', 'd']:
                    scores['kinesthetic'] += 1
            elif question in ['q3', 'q6', 'q9']:
                if answer in ['c', 'd']:
                    scores['kinesthetic'] += 1
                elif answer in ['a', 'b']:
                    scores['reading_writing'] += 1
        
        # Determine dominant style
        dominant_style = max(scores, key=scores.get)
        confidence = scores[dominant_style] / sum(scores.values()) if sum(scores.values()) > 0 else 0.5
        
        return {
            'dominant_style': dominant_style,
            'scores': scores,
            'confidence': round(confidence, 2)
        }
    
    def generate_learning_path(self, user_profile, topic):
        """
        Generate personalized learning path based on user profile
        """
        learning_path = []
        current_difficulty = user_profile.get('current_level', 'beginner')
        learning_style = user_profile.get('learning_style', 'visual')
        
        # Get courses for the topic
        topic_courses = self.course_database.get(topic, {})
        
        # Generate path based on learning style and difficulty
        for difficulty in ['beginner', 'intermediate', 'advanced']:
            if difficulty not in topic_courses:
                continue
                
            courses = topic_courses[difficulty]
            
            # Sort courses by learning style preference
            prioritized_courses = self._prioritize_by_style(courses, learning_style)
            
            for course in prioritized_courses:
                course_entry = {
                    **course,
                    'style_adapted': True,
                    'estimated_time': self._calculate_adapted_time(course, learning_style),
                    'prerequisites': self._get_prerequisites(course, courses)
                }
                learning_path.append(course_entry)
        
        return learning_path
    
    def _prioritize_by_style(self, courses, learning_style):
        """Prioritize content based on learning style"""
        style_priority = {
            'visual': ['video', 'interactive', 'article'],
            'auditory': ['video', 'article', 'interactive'],
            'reading_writing': ['article', 'quiz', 'video'],
            'kinesthetic': ['interactive', 'project', 'quiz']
        }
        
        preferred_types = style_priority.get(learning_style, ['video', 'article'])
        
        # Sort courses by preference
        sorted_courses = sorted(courses, key=lambda x: preferred_types.index(x['type']) 
                               if x['type'] in preferred_types else len(preferred_types))
        
        return sorted_courses
    
    def _calculate_adapted_time(self, course, learning_style):
        """Calculate adapted time based on learning style"""
        base_time = course['duration']
        
        # Adjust time based on learning style
        style_adjustments = {
            'visual': 0.9,  # Visual learners process video faster
            'auditory': 1.0,
            'reading_writing': 1.1,  # May need more time for reading
            'kinesthetic': 0.85  # Interactive learners learn faster through practice
        }
        
        return int(base_time * style_adjustments.get(learning_style, 1.0))
    
    def _get_prerequisites(self, course, courses):
        """Determine prerequisites for a course"""
        course_index = courses.index(course)
        if course_index > 0:
            return [courses[course_index - 1]['id']]
        return []
    
    def adapt_content_difficulty(self, user_progress, current_difficulty):
        """
        Adapt content difficulty based on user progress
        Returns recommended difficulty level
        """
        if user_progress['completion_rate'] > 0.8 and user_progress['avg_score'] > 0.85:
            return 'advanced'
        elif user_progress['completion_rate'] > 0.5 and user_progress['avg_score'] > 0.7:
            return 'intermediate'
        else:
            return current_difficulty
    
    def get_recommendations(self, user_history, user_profile):
        """Generate content recommendations based on user history"""
        recommendations = []
        
        # Analyze completed content
        completed_topics = set(item['topic'] for item in user_history)
        completed_courses = set(item['course_id'] for item in user_history)
        
        # Find related courses
        for topic in completed_topics:
            if topic in self.course_database:
                topic_courses = self.course_database[topic]
                for difficulty, courses in topic_courses.items():
                    for course in courses:
                        if course['id'] not in completed_courses:
                            recommendations.append({
                                **course,
                                'reason': f'Next step in {topic}',
                                'match_score': self._calculate_match_score(course, user_profile)
                            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _calculate_match_score(self, course, user_profile):
        """Calculate how well a course matches user profile"""
        score = 0
        
        # Learning style match
        style_priority = {
            'visual': ['video', 'interactive'],
            'auditory': ['video', 'article'],
            'reading_writing': ['article', 'quiz'],
            'kinesthetic': ['interactive', 'project']
        }
        
        preferred = style_priority.get(user_profile.get('learning_style', 'visual'), [])
        if course['type'] in preferred:
            score += 3
        
        # Difficulty match
        if course['difficulty'] == user_profile.get('current_level', 'beginner'):
            score += 2
        
        return score