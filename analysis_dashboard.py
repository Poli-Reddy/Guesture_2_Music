import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import seaborn as sns
import matplotlib.pyplot as plt
from recording_system import SessionManager
import time

class MusicAnalysisDashboard:
    """Advanced music analysis dashboard with comprehensive visualizations"""
    
    def __init__(self, sessions_dir="sessions"):
        self.session_manager = SessionManager(sessions_dir)
        self.setup_page_config()
    
    def setup_page_config(self):
        """Configure Streamlit page for analysis dashboard"""
        st.set_page_config(
            page_title="📊 GestureBeats Analytics",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for analytics dashboard
        st.markdown("""
        <style>
            .main {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            }
            
            .metric-card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                text-align: center;
                animation: fadeInUp 0.6s ease-out;
            }
            
            @keyframes fadeInUp {
                from { transform: translateY(30px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            .chart-container {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .session-card {
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 15px;
                padding: 15px;
                margin: 10px 0;
                color: white;
                cursor: pointer;
                transition: transform 0.3s ease;
            }
            
            .session-card:hover {
                transform: translateY(-5px);
            }
            
            .insight-box {
                background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                color: white;
                font-weight: bold;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def create_header(self):
        """Create dashboard header"""
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: white; font-size: 3em; margin: 0;">
                📊 GestureBeats Analytics
            </h1>
            <p style="color: #cccccc; font-size: 1.2em; margin: 10px 0;">
                Advanced Music Performance Analysis & Insights
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def create_overview_metrics(self):
        """Create overview metrics section"""
        st.markdown("### 📈 Performance Overview")
        
        all_stats = self.session_manager.get_all_stats()
        if not all_stats:
            st.info("No session data available. Record some sessions to see analytics!")
            return
        
        # Calculate aggregate metrics
        total_sessions = len(all_stats)
        total_duration = sum(stats['duration'] for stats in all_stats.values())
        total_events = sum(stats['total_events'] for stats in all_stats.values())
        avg_complexity = np.mean([stats['complexity_score'] for stats in all_stats.values()])
        avg_bpm = np.mean([stats['estimated_bpm'] for stats in all_stats.values() if stats['estimated_bpm'] > 0])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", total_sessions)
        
        with col2:
            st.metric("Total Duration", f"{total_duration:.1f}s")
        
        with col3:
            st.metric("Total Events", total_events)
        
        with col4:
            st.metric("Avg Complexity", f"{avg_complexity:.2f}")
    
    def create_session_selector(self):
        """Create session selection interface"""
        st.markdown("### 🎵 Session Analysis")
        
        sessions = self.session_manager.get_session_list()
        if not sessions:
            st.info("No sessions available for analysis.")
            return None
        
        # Session selection
        selected_session = st.selectbox(
            "Select Session to Analyze",
            sessions,
            format_func=lambda x: f"{x} ({self.session_manager.get_session_info(x)['duration']:.1f}s)"
        )
        
        return selected_session
    
    def create_gesture_analysis(self, session_id):
        """Create gesture analysis visualizations"""
        st.markdown("#### ✋ Gesture Analysis")
        
        stats = self.session_manager.get_session_stats(session_id)
        if not stats:
            return
        
        gesture_counts = stats.get('gesture_counts', {})
        if not gesture_counts:
            st.info("No gesture data available for this session.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gesture frequency bar chart
            fig = px.bar(
                x=list(gesture_counts.keys()),
                y=list(gesture_counts.values()),
                title="Gesture Usage Frequency",
                color=list(gesture_counts.values()),
                color_continuous_scale="viridis"
            )
            fig.update_layout(
                xaxis_title="Gesture",
                yaxis_title="Count",
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gesture distribution pie chart
            fig = px.pie(
                values=list(gesture_counts.values()),
                names=list(gesture_counts.keys()),
                title="Gesture Distribution"
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def create_hand_usage_analysis(self, session_id):
        """Create hand usage analysis"""
        st.markdown("#### 🖐️ Hand Usage Analysis")
        
        stats = self.session_manager.get_session_stats(session_id)
        if not stats:
            return
        
        hand_usage = stats.get('hand_usage', {})
        if not hand_usage:
            st.info("No hand usage data available.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Hand usage pie chart
            fig = px.pie(
                values=list(hand_usage.values()),
                names=list(hand_usage.keys()),
                title="Left vs Right Hand Usage",
                color_discrete_map={'left': '#ff6b6b', 'right': '#4ecdc4'}
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Hand usage metrics
            total_usage = sum(hand_usage.values())
            if total_usage > 0:
                left_percent = (hand_usage.get('left', 0) / total_usage) * 100
                right_percent = (hand_usage.get('right', 0) / total_usage) * 100
                
                st.metric("Left Hand Usage", f"{left_percent:.1f}%")
                st.metric("Right Hand Usage", f"{right_percent:.1f}%")
                
                # Balance indicator
                balance = abs(left_percent - right_percent)
                if balance < 10:
                    st.success("🎯 Well balanced hand usage!")
                elif balance < 25:
                    st.warning("⚖️ Moderately balanced")
                else:
                    st.info("📊 Unbalanced - consider using both hands more equally")
    
    def create_tempo_analysis(self, session_id):
        """Create tempo and rhythm analysis"""
        st.markdown("#### 🎵 Tempo & Rhythm Analysis")
        
        stats = self.session_manager.get_session_stats(session_id)
        if not stats:
            return
        
        estimated_bpm = stats.get('estimated_bpm', 0)
        complexity_score = stats.get('complexity_score', 0)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Estimated BPM", f"{estimated_bpm:.1f}")
        
        with col2:
            st.metric("Complexity Score", f"{complexity_score:.2f}")
        
        with col3:
            # Tempo classification
            if estimated_bpm < 80:
                tempo_class = "Slow"
                tempo_color = "blue"
            elif estimated_bpm < 120:
                tempo_class = "Moderate"
                tempo_color = "green"
            elif estimated_bpm < 160:
                tempo_class = "Fast"
                tempo_color = "orange"
            else:
                tempo_class = "Very Fast"
                tempo_color = "red"
            
            st.markdown(f"""
            <div style="background: {tempo_color}; padding: 10px; border-radius: 5px; text-align: center; color: white;">
                <strong>Tempo: {tempo_class}</strong>
            </div>
            """, unsafe_allow_html=True)
    
    def create_instrument_analysis(self, session_id):
        """Create instrument usage analysis"""
        st.markdown("#### 🎹 Instrument Analysis")
        
        stats = self.session_manager.get_session_stats(session_id)
        if not stats:
            return
        
        instruments_used = stats.get('instruments_used', [])
        if not instruments_used:
            st.info("No instrument data available.")
            return
        
        # Count instrument usage
        instrument_counts = Counter(instruments_used)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Instrument usage bar chart
            fig = px.bar(
                x=list(instrument_counts.keys()),
                y=list(instrument_counts.values()),
                title="Instrument Usage",
                color=list(instrument_counts.values()),
                color_continuous_scale="plasma"
            )
            fig.update_layout(
                xaxis_title="Instrument",
                yaxis_title="Usage Count",
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Instrument diversity
            diversity_score = len(set(instruments_used)) / len(instruments_used) if instruments_used else 0
            
            st.metric("Instrument Diversity", f"{diversity_score:.2f}")
            
            if diversity_score > 0.7:
                st.success("🎵 High instrument diversity!")
            elif diversity_score > 0.4:
                st.warning("🎶 Moderate diversity")
            else:
                st.info("🎹 Low diversity - try more instruments!")
    
    def create_performance_insights(self, session_id):
        """Create performance insights and recommendations"""
        st.markdown("#### 💡 Performance Insights")
        
        stats = self.session_manager.get_session_stats(session_id)
        if not stats:
            return
        
        insights = []
        
        # Gesture diversity insight
        gesture_counts = stats.get('gesture_counts', {})
        if len(gesture_counts) >= 4:
            insights.append("🎯 Great gesture diversity! You're using multiple gestures effectively.")
        elif len(gesture_counts) >= 2:
            insights.append("👍 Good gesture variety. Consider trying more gesture types.")
        else:
            insights.append("🔄 Try using more different gestures to create richer music.")
        
        # Hand balance insight
        hand_usage = stats.get('hand_usage', {})
        total_usage = sum(hand_usage.values())
        if total_usage > 0:
            left_percent = (hand_usage.get('left', 0) / total_usage) * 100
            right_percent = (hand_usage.get('right', 0) / total_usage) * 100
            balance = abs(left_percent - right_percent)
            
            if balance < 10:
                insights.append("⚖️ Excellent hand balance! Both hands are being used equally.")
            elif balance < 25:
                insights.append("🤝 Good hand coordination. Keep practicing with both hands.")
            else:
                dominant_hand = "left" if left_percent > right_percent else "right"
                insights.append(f"🖐️ Consider using your {dominant_hand} hand more to improve balance.")
        
        # Tempo insight
        estimated_bpm = stats.get('estimated_bpm', 0)
        if estimated_bpm > 0:
            if estimated_bpm < 80:
                insights.append("🐌 Slow tempo detected. Try increasing your playing speed.")
            elif estimated_bpm > 160:
                insights.append("⚡ Fast tempo! Great energy, but make sure you're maintaining control.")
            else:
                insights.append("🎵 Good tempo range! Your rhythm is well-balanced.")
        
        # Complexity insight
        complexity_score = stats.get('complexity_score', 0)
        if complexity_score > 0.7:
            insights.append("🌟 High complexity! You're creating sophisticated musical patterns.")
        elif complexity_score > 0.4:
            insights.append("🎼 Moderate complexity. Good balance of variety and consistency.")
        else:
            insights.append("🎹 Consider experimenting with more gesture-instrument combinations.")
        
        # Display insights
        for i, insight in enumerate(insights, 1):
            st.markdown(f"""
            <div class="insight-box">
                {i}. {insight}
            </div>
            """, unsafe_allow_html=True)
    
    def create_comparative_analysis(self):
        """Create comparative analysis across sessions"""
        st.markdown("#### 📊 Comparative Analysis")
        
        all_stats = self.session_manager.get_all_stats()
        if len(all_stats) < 2:
            st.info("Need at least 2 sessions for comparative analysis.")
            return
        
        # Create comparison dataframe
        comparison_data = []
        for session_id, stats in all_stats.items():
            comparison_data.append({
                'Session': session_id,
                'Duration': stats['duration'],
                'Events': stats['total_events'],
                'Complexity': stats['complexity_score'],
                'BPM': stats['estimated_bpm'],
                'Gestures': len(stats.get('gesture_counts', {})),
                'Instruments': len(stats.get('instruments_used', []))
            })
        
        df = pd.DataFrame(comparison_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Duration vs Events scatter plot
            fig = px.scatter(
                df, x='Duration', y='Events',
                title="Duration vs Events",
                hover_data=['Session', 'Complexity', 'BPM'],
                color='Complexity',
                color_continuous_scale='viridis'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Complexity vs BPM scatter plot
            fig = px.scatter(
                df, x='Complexity', y='BPM',
                title="Complexity vs Tempo",
                hover_data=['Session', 'Duration', 'Events'],
                color='Duration',
                color_continuous_scale='plasma'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Session comparison table
        st.markdown("##### Session Comparison Table")
        st.dataframe(df, use_container_width=True)
    
    def create_export_section(self):
        """Create data export section"""
        st.markdown("#### 📤 Export Data")
        
        sessions = self.session_manager.get_session_list()
        if not sessions:
            st.info("No sessions available for export.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_session = st.selectbox(
                "Select Session to Export",
                sessions,
                key="export_session"
            )
        
        with col2:
            export_format = st.selectbox(
                "Export Format",
                ["JSON", "CSV"],
                key="export_format"
            )
        
        if st.button("Export Session Data"):
            try:
                export_data = self.session_manager.export_session(
                    selected_session, 
                    export_format.lower()
                )
                
                if export_data:
                    st.download_button(
                        label=f"Download {export_format}",
                        data=export_data,
                        file_name=f"{selected_session}_export.{export_format.lower()}",
                        mime="application/json" if export_format == "JSON" else "text/csv"
                    )
                else:
                    st.error("Failed to export session data.")
            except Exception as e:
                st.error(f"Export error: {e}")
    
    def run(self):
        """Run the analysis dashboard"""
        self.create_header()
        
        # Sidebar
        with st.sidebar:
            st.markdown("### 🎛️ Dashboard Controls")
            
            # Refresh button
            if st.button("🔄 Refresh Data"):
                st.rerun()
            
            # Session management
            st.markdown("#### Session Management")
            sessions = self.session_manager.get_session_list()
            
            if sessions:
                st.write(f"**Available Sessions:** {len(sessions)}")
                
                # Delete session option
                session_to_delete = st.selectbox(
                    "Delete Session",
                    ["None"] + sessions,
                    key="delete_session"
                )
                
                if session_to_delete != "None" and st.button("🗑️ Delete"):
                    if self.session_manager.delete_session(session_to_delete):
                        st.success(f"Deleted session: {session_to_delete}")
                        st.rerun()
                    else:
                        st.error("Failed to delete session")
            else:
                st.info("No sessions available")
        
        # Main content
        self.create_overview_metrics()
        
        # Session analysis
        selected_session = self.create_session_selector()
        
        if selected_session:
            # Create tabs for different analysis sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🎵 Performance", "✋ Gestures", "🖐️ Hands", "🎹 Instruments", "💡 Insights"
            ])
            
            with tab1:
                self.create_tempo_analysis(selected_session)
            
            with tab2:
                self.create_gesture_analysis(selected_session)
            
            with tab3:
                self.create_hand_usage_analysis(selected_session)
            
            with tab4:
                self.create_instrument_analysis(selected_session)
            
            with tab5:
                self.create_performance_insights(selected_session)
        
        # Comparative analysis
        st.markdown("---")
        self.create_comparative_analysis()
        
        # Export section
        st.markdown("---")
        self.create_export_section()

def main():
    """Main function to run the analysis dashboard"""
    dashboard = MusicAnalysisDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
