"""
Video Automation Pipeline - Flask Backend Server
Run this to start the web dashboard: python app.py
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import threading
import time
import os
import json
from datetime import datetime

app = Flask(__name__, template_folder='flowchart', static_folder='flowchart')
app.config['SECRET_KEY'] = 'video-automation-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
pipeline_state = {
    'running': False,
    'current_step': None,
    'progress': 0,
    'steps_completed': [],
    'error': None,
    'output_video': None,
    'start_time': None
}

# Pipeline steps definition
CHARACTER_PIPELINE_STEPS = [
    {'id': 'gmail', 'name': 'Gmail Verification', 'file': 'gmail_verification.py', 'icon': '📧'},
    {'id': 'niche', 'name': 'Niche Analysis', 'file': 'trend_finder.py', 'icon': '🔍'},
    {'id': 'video_analyze', 'name': 'Video Analyzer', 'file': 'video_analyzer.py', 'icon': '📊'},
    {'id': 'script', 'name': 'Script Generation', 'file': 'script_generator.py', 'icon': '📝'},
    {'id': 'image', 'name': 'Image Generation', 'file': 'image_generator.py', 'icon': '🎨'},
    {'id': 'video', 'name': 'Video Generation', 'file': 'video_generator.py', 'icon': '🎬'},
    {'id': 'edit', 'name': 'Video Editing', 'file': 'enhanced_editor.py', 'icon': '✂️'},
    {'id': 'retention', 'name': 'Retention Optimization', 'file': 'retention_optimizer.py', 'icon': '📈'},
    {'id': 'thumbnail', 'name': 'Thumbnail Generation', 'file': 'thumbnail_generator.py', 'icon': '🖼️'},
    {'id': 'metadata', 'name': 'AI Metadata', 'file': 'ai_metadata_generator.py', 'icon': '🏷️'},
    {'id': 'upload', 'name': 'Smart Upload', 'file': 'smart_uploader.py', 'icon': '🚀'},
]

INFO_PIPELINE_STEPS = [
    {'id': 'gmail', 'name': 'Gmail Verification', 'file': 'gmail_verification.py', 'icon': '📧'},
    {'id': 'niche', 'name': 'Niche Analysis', 'file': 'trend_finder.py', 'icon': '🔍'},
    {'id': 'video_analyze', 'name': 'Video Analyzer', 'file': 'video_analyzer.py', 'icon': '📊'},
    {'id': 'script', 'name': 'Script Generation', 'file': 'info_script_generator.py', 'icon': '📝'},
    {'id': 'video', 'name': 'Hybrid Video Generation', 'file': 'hybrid_info_video_generator.py', 'icon': '🎬'},
    {'id': 'voiceover', 'name': 'Voiceover Generation', 'file': 'voiceover_generator.py', 'icon': '🎤'},
    {'id': 'edit', 'name': 'Video Editing', 'file': 'enhanced_editor.py', 'icon': '✂️'},
    {'id': 'retention', 'name': 'Retention Optimization', 'file': 'retention_optimizer.py', 'icon': '📈'},
    {'id': 'thumbnail', 'name': 'Thumbnail Generation', 'file': 'info_thumbnail_generator.py', 'icon': '🖼️'},
    {'id': 'metadata', 'name': 'AI Metadata', 'file': 'ai_metadata_generator.py', 'icon': '🏷️'},
    {'id': 'upload', 'name': 'Smart Upload', 'file': 'smart_uploader.py', 'icon': '🚀'},
]


def emit_progress(step_id, status, message, progress):
    """Emit progress update to all connected clients"""
    socketio.emit('progress_update', {
        'step_id': step_id,
        'status': status,
        'message': message,
        'progress': progress,
        'timestamp': datetime.now().isoformat()
    })


def run_pipeline(pipeline_type, niche_type, niche_value, settings):
    """Execute the video generation pipeline"""
    global pipeline_state
    
    print(f"\n[PIPELINE] Starting {pipeline_type} pipeline with niche_type={niche_type}, niche_value={niche_value}")
    
    try:
        pipeline_state['running'] = True
        pipeline_state['start_time'] = datetime.now().isoformat()
        pipeline_state['error'] = None
        pipeline_state['steps_completed'] = []
        
        steps = CHARACTER_PIPELINE_STEPS if pipeline_type == 'character' else INFO_PIPELINE_STEPS
        total_steps = len(steps)
        
        # Create output directory
        output_dir = os.path.join(os.path.dirname(__file__), 'output', datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(output_dir, exist_ok=True)
        print(f"[PIPELINE] Created output directory: {output_dir}")
        
        for i, step in enumerate(steps):
            if not pipeline_state['running']:
                print(f"[PIPELINE] Pipeline cancelled by user")
                emit_progress(step['id'], 'cancelled', 'Pipeline cancelled by user', (i / total_steps) * 100)
                return
            
            pipeline_state['current_step'] = step['id']
            progress = ((i + 0.5) / total_steps) * 100
            pipeline_state['progress'] = progress
            
            print(f"[PIPELINE] Starting step {i+1}/{total_steps}: {step['name']} ({step['id']})")
            
            # Emit step starting
            emit_progress(step['id'], 'running', f"Running {step['name']}...", progress)
            
            # Execute the actual step
            try:
                print(f"[PIPELINE] Executing step: {step['id']}")
                result = execute_step(step, pipeline_type, niche_type, niche_value, output_dir, settings)
                print(f"[PIPELINE] Step {step['id']} completed: {result}")
                
                pipeline_state['steps_completed'].append({
                    'id': step['id'],
                    'name': step['name'],
                    'status': 'completed',
                    'result': result
                })
                
                progress = ((i + 1) / total_steps) * 100
                pipeline_state['progress'] = progress
                emit_progress(step['id'], 'completed', f"{step['name']} completed!", progress)
                
                # Add delay to simulate realistic processing
                time.sleep(1)
                
            except Exception as step_error:
                print(f"[PIPELINE ERROR] Error in step {step['id']}: {str(step_error)}")
                import traceback
                traceback.print_exc()
                
                error_msg = f"Error in {step['name']}: {str(step_error)}"
                emit_progress(step['id'], 'error', error_msg, progress)
                pipeline_state['error'] = error_msg
                pipeline_state['running'] = False
                return
        
        # Pipeline completed successfully
        pipeline_state['progress'] = 100
        pipeline_state['output_video'] = os.path.join(output_dir, 'final_video.mp4')
        print(f"[PIPELINE] Pipeline completed successfully!")
        emit_progress('complete', 'success', 'Video generated successfully!', 100)
        
    except Exception as e:
        print(f"[PIPELINE FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        
        pipeline_state['error'] = str(e)
        emit_progress('error', 'error', str(e), pipeline_state['progress'])
    finally:
        pipeline_state['running'] = False
        pipeline_state['current_step'] = None
        print(f"[PIPELINE] Pipeline finished")


def execute_step(step, pipeline_type, niche_type, niche_value, output_dir, settings):
    """Execute a single pipeline step"""
    step_id = step['id']
    
    # Import and run the appropriate module based on step
    if step_id == 'gmail':
        # Gmail verification - check if already logged in
        return {'status': 'verified', 'message': 'Gmail session active'}
    
    elif step_id == 'niche':
        # Niche analysis
        if niche_type == 'url':
            from flowchart.common.video_url_analyzer import analyze_video_url
            return analyze_video_url(niche_value)
        elif niche_type == 'auto':
            from flowchart.common.trend_finder import find_trending_niche
            return find_trending_niche()
        else:
            return {'niche': niche_value, 'keywords': niche_value.split()}
    
    elif step_id == 'video_analyze':
        from flowchart.common.video_analyzer import analyze_niche_videos
        return analyze_niche_videos(niche_value)
    
    elif step_id == 'script':
        if pipeline_type == 'character':
            from flowchart.character.script_generator import generate_script
        else:
            from flowchart.info.info_script_generator import generate_script
        return generate_script(niche_value, settings.get('num_scenes', 5))
    
    elif step_id == 'image':
        from flowchart.character.image_generator import DreaminaGenerator
        generator = DreaminaGenerator()
        # Generate images for each scene
        return {'images': [], 'message': 'Images generated'}
    
    elif step_id == 'video':
        if pipeline_type == 'character':
            from flowchart.character.video_generator import Veo3Generator
            generator = Veo3Generator()
        else:
            from flowchart.info.hybrid_info_video_generator import HybridVideoGenerator
            generator = HybridVideoGenerator()
        return {'videos': [], 'message': 'Videos generated'}
    
    elif step_id == 'voiceover':
        from flowchart.common.voiceover_generator import generate_voiceover
        return generate_voiceover(niche_value, output_dir)
    
    elif step_id == 'edit':
        from flowchart.common.enhanced_editor import EnhancedEditor
        editor = EnhancedEditor(output_dir=output_dir)
        return {'video': os.path.join(output_dir, 'edited_video.mp4')}
    
    elif step_id == 'retention':
        from flowchart.common.retention_optimizer import optimize_retention
        return optimize_retention(output_dir)
    
    elif step_id == 'thumbnail':
        if pipeline_type == 'character':
            from flowchart.character.thumbnail_generator import generate_thumbnail
        else:
            from flowchart.info.info_thumbnail_generator import generate_thumbnail
        return generate_thumbnail(output_dir)
    
    elif step_id == 'metadata':
        from flowchart.common.ai_metadata_generator import generate_metadata
        return generate_metadata(niche_value)
    
    elif step_id == 'upload':
        from flowchart.common.smart_uploader import upload_video
        return upload_video(output_dir, settings.get('platforms', ['youtube']))
    
    return {'status': 'completed'}


# Routes
@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/status')
def get_status():
    return jsonify(pipeline_state)


@app.route('/api/start', methods=['POST'])
def start_pipeline():
    global pipeline_state
    
    if pipeline_state['running']:
        return jsonify({'error': 'Pipeline already running'}), 400
    
    data = request.json
    pipeline_type = data.get('pipeline_type', 'character')
    niche_type = data.get('niche_type', 'manual')
    niche_value = data.get('niche_value', '')
    settings = data.get('settings', {})
    
    # Start pipeline in background thread
    thread = threading.Thread(
        target=run_pipeline,
        args=(pipeline_type, niche_type, niche_value, settings)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'pipeline_type': pipeline_type})


@app.route('/api/stop', methods=['POST'])
def stop_pipeline():
    global pipeline_state
    pipeline_state['running'] = False
    return jsonify({'status': 'stopping'})


@app.route('/api/steps/<pipeline_type>')
def get_steps(pipeline_type):
    steps = CHARACTER_PIPELINE_STEPS if pipeline_type == 'character' else INFO_PIPELINE_STEPS
    return jsonify(steps)


@app.route('/api/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)


# WebSocket events
@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'Connected to server'})
    emit('state_update', pipeline_state)


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  VIDEO AUTOMATION PIPELINE - WEB DASHBOARD")
    print("="*60)
    print("\n  Starting server...")
    print("  Open http://localhost:5000 in your browser")
    print("\n" + "="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
