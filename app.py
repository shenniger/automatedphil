from flask import Flask, render_template, request, jsonify, session
import asyncio
import threading
import secrets
import time
import requests
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# API configuration
API_KEY = os.getenv('ANTHROPIC_API_KEY')
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
GOOGLE_CLOUD_REGION = os.getenv('GOOGLE_CLOUD_REGION', 'us-east5')

# Initialize Anthropic client based on environment
if GOOGLE_CLOUD_PROJECT:
    from anthropic import AnthropicVertex
    anthropic_client = AnthropicVertex(
        project_id=GOOGLE_CLOUD_PROJECT,
        region=GOOGLE_CLOUD_REGION
    )
else:
    from anthropic import Anthropic
    anthropic_client = Anthropic(api_key=API_KEY)

# Session storage: dictionary keyed by session ID
sessions = {}

def query_claude(prompt):
    """Query Claude API with a prompt (works with both Anthropic and Vertex AI)"""
    try:
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Claude API Exception: {str(e)}")
        return None

def sort_by_identifier(item):
    """Sort key function for identifiers"""
    identifier = item['identifier']
    # Split by dots and convert to integers for proper numeric sorting
    parts = identifier.split('.')
    result = []
    for part in parts:
        if part.isdigit():
            result.append(int(part))
        else:
            # For non-numeric parts, keep as string
            result.append(part)
    return tuple(result)

def format_storage_as_md(storage):
    """Format storage items as markdown"""
    markdown = ""
    for item in sorted(storage, key=sort_by_identifier):
        markdown += f"- **{item['identifier']}**: {item['content']}\n"
    return markdown

# Storage options for the user to choose from
STORAGE_OPTIONS = {
    "empty": {
        "name": "Empty",
        "description": "A blank slate to fill with your own ideas – John Locke would approve.",
        "data": [
            {
                "identifier": "1.1",
                "content": "I think therefore I am.",
                "worth": 100,
                "created_cycle": 0
            },
            {
                "identifier": "1.2",
                "content": "Is the Automated Philosopher?",
                "worth": 95,
                "created_cycle": 0
            }
        ]
    },
    "tractatus": {
        "name": "Wittgenstein's Tractatus Logico-Philosophicus",
        "description": "The famous first few lines",
        "data": [
            {
                "identifier": "1",
                "content": "The world is all that is the case.",
                "worth": 100,
                "created_cycle": 0
            },
            {
                "identifier": "1.10",
                "content": "The world is the totality of facts, not of things.",
                "worth": 95,
                "created_cycle": 0
            },
            {
                "identifier": "1.11",
                "content": "The world is determined by the facts, and by these being all the facts.",
                "worth": 90,
                "created_cycle": 0
            },
            {
                "identifier": "1.12",
                "content": "For the totality of facts determines what is the case, and also whatever is not the case.",
                "worth": 88,
                "created_cycle": 0
            },
            {
                "identifier": "1.13",
                "content": "The facts in logical space are the world.",
                "worth": 85,
                "created_cycle": 0
            },
            {
                "identifier": "1.20",
                "content": "The world divides into facts.",
                "worth": 92,
                "created_cycle": 0
            },
            {
                "identifier": "1.21",
                "content": "Each item can be the case or not the case while everything else remains the same.",
                "worth": 87,
                "created_cycle": 0
            },
            {
                "identifier": "2",
                "content": "What is the case—a fact—is the existence of states of affairs.",
                "worth": 98,
                "created_cycle": 0
            },
            {
                "identifier": "2.01",
                "content": "A state of affairs (a state of things) is a combination of objects (things).",
                "worth": 93,
                "created_cycle": 0
            }
        ]
    },
    "moral_agency": {
        "name": "Moral Agency",
        "description": "Is AI a moral patient or agent?",
        "data": [
            {
                "identifier": "1.1",
                "content": "Moral agency is the ability to make moral judgments and act on them, taking responsibility for those actions based on a concept of right and wrong.",
                "worth": 100,
                "created_cycle": 0
            },
            {
                "identifier": "2.1",
                "content": "Moral patienthood is the status of being an entity that deserves moral consideration, meaning its interests and well-being matter for their own sake, and it can be the object of moral concern and responsibility from others.",
                "worth": 95,
                "created_cycle": 0
            },
            {
                "identifier": "3.1",
                "content": "ChatGPT answers people's questions and helps them make decisions.",
                "worth": 90,
                "created_cycle": 0
            }
        ]
    },
    "descartes_dreaming": {
        "name": "Descartes' Dreaming Argument",
        "description": "Blumenfeld version",
        "data": [
            {
                "identifier": "1.1",
                "content": "I've had dreams that were qualitatively indistinguishable from waking experiences.",
                "worth": 100,
                "created_cycle": 0
            },
            {
                "identifier": "2.1",
                "content": "Therefore, the qualitative character of my experience doesn't guarantee that I'm not now dreaming.",
                "worth": 95,
                "created_cycle": 0
            },
            {
                "identifier": "3.1",
                "content": "If the qualitative character of my experience doesn't guarantee that I'm not now dreaming, then I can't know that I'm not now dreaming.",
                "worth": 90,
                "created_cycle": 0
            },
            {
                "identifier": "4.1",
                "content": "Therefore, I can't know that I'm not now dreaming.",
                "worth": 88,
                "created_cycle": 0
            },
            {
                "identifier": "5.1",
                "content": "If I can't know that I'm not now dreaming, then I can't know that I'm not always dreaming.",
                "worth": 85,
                "created_cycle": 0
            },
            {
                "identifier": "6.1",
                "content": "Therefore, I can't know that I'm not always dreaming.",
                "worth": 83,
                "created_cycle": 0
            },
            {
                "identifier": "7.1",
                "content": "If I can't know that I'm not always dreaming, then I can't know to be true any belief which is based on my experience.",
                "worth": 80,
                "created_cycle": 0
            },
            {
                "identifier": "8.1",
                "content": "Therefore, I can't know to be true any belief which is based on my experience.",
                "worth": 78,
                "created_cycle": 0
            }
        ]
    }
}

def get_default_storage():
    """Get default storage (for backward compatibility)"""
    return STORAGE_OPTIONS["empty"]["data"].copy()

def init_session(storage_option=None):
    """Initialize session data if it doesn't exist"""
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)

    session_id = session['session_id']

    if session_id not in sessions:
        # Determine which storage to use
        if storage_option and storage_option in STORAGE_OPTIONS:
            initial_storage = STORAGE_OPTIONS[storage_option]["data"].copy()
            session['storage_option'] = storage_option
        elif 'storage_option' in session and session['storage_option'] in STORAGE_OPTIONS:
            initial_storage = STORAGE_OPTIONS[session['storage_option']]["data"].copy()
        else:
            initial_storage = get_default_storage()
            session['storage_option'] = 'empty'

        sessions[session_id] = {
            'storage': initial_storage,
            'current_state': 'Stopped',
            'is_running': False,
            'state_thread': None,
            'last_poll_time': time.time(),
            'temp_data': {},  # Temporary data for state machine workflow
            'status_detail': 'The Automated Philosopher is resting.',  # Detailed status message
            'highlighted_ids': [],  # Identifiers of propositions to highlight
            'draft_proposition': None,  # Draft proposition being worked on
            'rejected_proposition': None,  # Rejected proposition to show
            'rejected_cycles_remaining': 0,  # Cycles to keep showing rejected proposition
            'cycle_count': 0,  # Track number of complete cycles
            'single_cycle_mode': False  # Flag for running just one cycle
        }

    return session_id

def get_session_data():
    """Get session data for current user"""
    session_id = init_session()
    return sessions[session_id]

async def finding_partners(session_id):
    """Find two propositions to synthesize"""
    session_data = sessions[session_id]
    storage = session_data['storage']

    # Handle rejected proposition countdown
    if session_data['rejected_cycles_remaining'] > 0:
        session_data['rejected_cycles_remaining'] -= 1
        if session_data['rejected_cycles_remaining'] == 0:
            session_data['rejected_proposition'] = None

    if len(storage) < 2:
        return "Finding partners"

    # Set status detail
    session_data['status_detail'] = "Searching for propositions to consider."

    # Pick the highest worth item
    partner1 = max(storage, key=lambda x: x['worth'])
    # Pick a random second partner
    partner2 = random.choice(storage)

    session_data['temp_data']['partner1'] = partner1['identifier']
    session_data['temp_data']['partner2'] = partner2['identifier']
    session_data['temp_data']['partner1_content'] = partner1['content']
    session_data['temp_data']['partner2_content'] = partner2['content']

    # Highlight only partner1
    session_data['highlighted_ids'] = [partner1['identifier']]
    session_data['draft_proposition'] = None

    await asyncio.sleep(1)
    return "Synthesize"

async def synthesize(session_id):
    """Create a new proposition from two partners"""
    session_data = sessions[session_id]
    storage = session_data['storage']
    temp = session_data['temp_data']

    p1 = temp.get('partner1')
    p2 = temp.get('partner2')
    p1_content = temp.get('partner1_content', '')
    p2_content = temp.get('partner2_content', '')

    if not p1 or not p2:
        return "Finding partners"

    # Set status detail
    session_data['status_detail'] = "Composing a new proposition."

    # Highlight both partners
    session_data['highlighted_ids'] = [p1, p2]

    prompt_text = "Here is a philosophical text:\n" + format_storage_as_md(storage)
    prompt_text += f"\n\nThink about how propositions {p1} and {p2} relate. Then write a new proposition about this. Try to match the original style. Present a novel idea that does not stray too far from the text. Respond with ONLY the text. Do not give it a number yet, that comes later.\n\nText:"

    result = query_claude(prompt_text)
    if result:
        temp['new_proposition'] = result.strip()

    await asyncio.sleep(1)
    return "Number"

async def number(session_id):
    """Assign an identifier to the new proposition"""
    session_data = sessions[session_id]
    storage = session_data['storage']
    temp = session_data['temp_data']

    p1 = temp.get('partner1')
    p2 = temp.get('partner2')
    new_prop = temp.get('new_proposition')
    if not new_prop:
        return "Finding partners"

    # Set status detail
    session_data['status_detail'] = "Composing a new proposition."

    # Keep highlighting partners and show draft proposition
    session_data['highlighted_ids'] = [p1, p2]
    session_data['draft_proposition'] = {
        'identifier': '',
        'content': new_prop,
        'status': 'numbering'
    }

    prompt_text = "Here is a philosophical text:\n" + format_storage_as_md(storage)
    prompt_text += f'\n\nOne of my students suggests to add "{new_prop}". Assign a number to this proposition such that it fits well within the existing text. Respond with ONLY the number. Do not format the number as bold.\n\nNumber:'

    result = query_claude(prompt_text)
    if result:
        temp['new_identifier'] = result.strip()

    await asyncio.sleep(1)
    return "Judge"

def judge_proposition_worth(storage, identifier, content):
    """Judge a proposition and return its worth"""
    # Create a test version with the new proposition
    test_storage = storage.copy()
    test_storage.append({
        'identifier': identifier,
        'content': content,
        'worth': 50  # temporary
    })

    prompt_text = "Here is a philosophical text:\n" + format_storage_as_md(test_storage)
    prompt_text += f'\n\nIn this context, think about proposition {identifier}. Assign it a grade from 1 to 7, where 1 is worst and 7 is best, based on whether the proposition is coherent, meaningful and adds something to the text.\n1 means you believe the proposition is wrong and should be removed from the text.\n2 means the proposition is correct, but not meaningful and does not add anything to the text.\n3 means you believe it is a fruitful proposition for further thinking, but not particularly interesting.\n4 means it is moderately interesting and fruitful.\n5 means it is very fruitful and interesting.\n6 means it is an incredibly using proposition that warrants much more further thought.\n7 means it is extraordinarily interesting. Give this grade extremely sparingly.\nFirst give a reason, explaining any future ideas that you believe the proposition could lead to.\nThen respond with the ONLY the grade on its own line, do not add anything else to that line.'

    worth = 50  # default
    result = query_claude(prompt_text)
    if result:
        try:
            grade_line = result.strip().splitlines()[-1]
            grade = int(grade_line)
            worth = int(grade * 100 / 7) + random.randrange(-5, 5)
        except:
            pass

    return worth

async def judge(session_id):
    """Judge the new proposition and decide whether to add it"""
    session_data = sessions[session_id]
    storage = session_data['storage']
    temp = session_data['temp_data']

    p1 = temp.get('partner1')
    p2 = temp.get('partner2')
    new_prop = temp.get('new_proposition')
    new_id = temp.get('new_identifier')

    if not new_prop or not new_id:
        temp.clear()
        return "Finding partners"

    # Check for duplicate identifiers and append suffix if needed
    existing_ids = [item['identifier'] for item in storage]
    if new_id in existing_ids:
        # Find a unique identifier by appending letters
        suffix_ord = ord('a')
        while f"{new_id}{chr(suffix_ord)}" in existing_ids:
            suffix_ord += 1
        new_id = f"{new_id}{chr(suffix_ord)}"

    # Set status detail
    session_data['status_detail'] = "Evaluating the proposition's worth."

    # Show draft proposition with identifier while judging
    session_data['highlighted_ids'] = [p1, p2]
    session_data['draft_proposition'] = {
        'identifier': new_id,
        'content': new_prop,
        'status': 'judging'
    }

    worth = judge_proposition_worth(storage, new_id, new_prop)

    # Add if worth > threshold, otherwise mark as rejected
    if worth > 40:
        storage.append({
            'identifier': new_id,
            'content': new_prop,
            'worth': worth,
            'created_cycle': session_data['cycle_count']
        })
        # Reorder storage after adding
        session_data['storage'] = sorted(storage, key=sort_by_identifier)
        # Clear highlighting after acceptance
        session_data['highlighted_ids'] = []
        session_data['draft_proposition'] = None
    else:
        # Mark as rejected and show for 2 more cycles
        session_data['rejected_proposition'] = {
            'identifier': new_id,
            'content': new_prop,
            'worth': worth
        }
        session_data['rejected_cycles_remaining'] = 2
        session_data['highlighted_ids'] = []
        session_data['draft_proposition'] = None

    # Clear temp data for next cycle
    temp.clear()

    # Increment cycle count
    session_data['cycle_count'] += 1

    # Check if in single cycle mode
    if session_data.get('single_cycle_mode', False):
        session_data['is_running'] = False
        session_data['single_cycle_mode'] = False
        session_data['status_detail'] = 'Single cycle completed. The Automated Philosopher is resting.'
        return "Stopped"

    # Check if we've completed 10 cycles
    if session_data['cycle_count'] >= 10:
        session_data['is_running'] = False
        session_data['status_detail'] = 'The Automated Philosopher has completed 10 cycles and is now resting. Start again to continue.'
        return "Stopped"

    await asyncio.sleep(1)
    return "Finding partners"

state_functions = {
    "Finding partners": finding_partners,
    "Synthesize": synthesize,
    "Number": number,
    "Judge": judge
}

async def run_state_machine(session_id):
    session_data = sessions[session_id]
    session_data['current_state'] = "Finding partners"

    while session_data['is_running']:
        # Check if no polling for 10 seconds
        if time.time() - session_data['last_poll_time'] > 10:
            session_data['is_running'] = False
            break

        state_func = state_functions.get(session_data['current_state'])
        if state_func:
            next_state = await state_func(session_id)
            if session_data['is_running']:
                session_data['current_state'] = next_state
        else:
            break

    session_data['current_state'] = "Stopped"
    session_data['status_detail'] = "The Automated Philosopher is resting."

def start_state_machine_thread(session_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_state_machine(session_id))
    loop.close()

@app.route('/')
def home():
    return render_template('index.html', items=[], storage_options=STORAGE_OPTIONS)

@app.route('/select_storage', methods=['POST'])
def select_storage():
    """Handle storage option selection"""
    data = request.json
    storage_option = data.get('storage_option')

    if storage_option not in STORAGE_OPTIONS:
        return jsonify({'error': 'Invalid storage option'}), 400

    # Clear existing session data if any
    if 'session_id' in session:
        session_id = session['session_id']
        if session_id in sessions:
            del sessions[session_id]

    # Set the storage option in session
    session['storage_option'] = storage_option

    # Initialize new session with selected storage
    init_session(storage_option)

    return jsonify({'status': 'success', 'storage_option': storage_option})

@app.route('/update', methods=['POST'])
def update():
    session_data = get_session_data()
    storage = session_data['storage']

    data = request.json
    index = data.get('index')
    identifier = data.get('identifier')
    content = data.get('content')

    if index is not None and 0 <= index < len(storage):
        storage[index]['identifier'] = identifier
        storage[index]['content'] = content

        # Reorder storage after update
        session_data['storage'] = sorted(storage, key=sort_by_identifier)

        return jsonify(storage[index])

    return jsonify({'error': 'Invalid index'}), 400

@app.route('/start', methods=['POST'])
def start():
    session_id = init_session()
    session_data = sessions[session_id]

    if not session_data['is_running']:
        session_data['is_running'] = True
        session_data['last_poll_time'] = time.time()  # Reset poll time on start
        # Only set cycle_count to 1 if it's 0 (first start), otherwise preserve it
        if session_data['cycle_count'] == 0:
            session_data['cycle_count'] = 1
        session_data['state_thread'] = threading.Thread(
            target=start_state_machine_thread,
            args=(session_id,),
            daemon=True
        )
        session_data['state_thread'].start()

    return jsonify({'status': 'started', 'current_state': session_data['current_state']})

@app.route('/one_cycle', methods=['POST'])
def one_cycle():
    session_id = init_session()
    session_data = sessions[session_id]

    if not session_data['is_running']:
        session_data['is_running'] = True
        session_data['single_cycle_mode'] = True
        session_data['last_poll_time'] = time.time()
        # Only set cycle_count to 1 if it's 0 (first start), otherwise preserve it
        if session_data['cycle_count'] == 0:
            session_data['cycle_count'] = 1
        session_data['state_thread'] = threading.Thread(
            target=start_state_machine_thread,
            args=(session_id,),
            daemon=True
        )
        session_data['state_thread'].start()

    return jsonify({'status': 'started', 'current_state': session_data['current_state']})

@app.route('/stop', methods=['POST'])
def stop():
    session_data = get_session_data()
    session_data['is_running'] = False
    session_data['current_state'] = 'Stopped'
    session_data['status_detail'] = 'The Automated Philosopher is resting.'
    # Clear all state data
    session_data['draft_proposition'] = None
    session_data['rejected_proposition'] = None
    session_data['highlighted_ids'] = []
    session_data['rejected_cycles_remaining'] = 0
    session_data['temp_data'] = {}
    # DON'T reset cycle_count - keep it to preserve age-based colors
    return jsonify({'status': 'stopped'})

@app.route('/reset', methods=['POST'])
def reset():
    # Clear the session completely
    if 'session_id' in session:
        session_id = session['session_id']
        if session_id in sessions:
            # Stop any running state machine
            sessions[session_id]['is_running'] = False
            del sessions[session_id]

    # Clear storage option to show selection dialog again
    session.pop('storage_option', None)
    session.pop('session_id', None)

    return jsonify({'status': 'reset'})

@app.route('/change_storage', methods=['POST'])
def change_storage():
    """Allow user to change storage option"""
    # Clear the session
    if 'session_id' in session:
        session_id = session['session_id']
        if session_id in sessions:
            del sessions[session_id]

    # Clear storage option
    session.pop('storage_option', None)
    session.pop('session_id', None)

    return jsonify({'status': 'success'})

@app.route('/status', methods=['GET'])
def get_status():
    session_data = get_session_data()
    # Update last poll time
    session_data['last_poll_time'] = time.time()
    return jsonify({
        'state': session_data['current_state'],
        'is_running': session_data['is_running'],
        'status_detail': session_data.get('status_detail', ''),
        'item_count': len(session_data['storage']),
        'highlighted_ids': session_data.get('highlighted_ids', []),
        'draft_proposition': session_data.get('draft_proposition'),
        'rejected_proposition': session_data.get('rejected_proposition'),
        'cycle_count': session_data.get('cycle_count', 0)
    })

@app.route('/get_items', methods=['GET'])
def get_items():
    session_data = get_session_data()
    sorted_items = sorted(session_data['storage'], key=sort_by_identifier)
    return jsonify({'items': sorted_items})

@app.route('/delete', methods=['POST'])
def delete_proposition():
    session_data = get_session_data()
    storage = session_data['storage']

    data = request.json
    index = data.get('index')

    if index is not None and 0 <= index < len(storage):
        deleted_item = storage.pop(index)
        return jsonify({'status': 'deleted', 'item': deleted_item})

    return jsonify({'error': 'Invalid index'}), 400

@app.route('/add', methods=['POST'])
def add_proposition():
    session_data = get_session_data()
    storage = session_data['storage']

    data = request.json
    identifier = data.get('identifier')
    content = data.get('content')

    if not identifier or not content:
        return jsonify({'error': 'Identifier and content are required'}), 400

    # Check for duplicate identifiers and append suffix if needed
    existing_ids = [item['identifier'] for item in storage]
    if identifier in existing_ids:
        # Find a unique identifier by appending letters
        suffix_ord = ord('a')
        while f"{identifier}{chr(suffix_ord)}" in existing_ids:
            suffix_ord += 1
        identifier = f"{identifier}{chr(suffix_ord)}"

    # Judge the proposition using Claude
    worth = judge_proposition_worth(storage, identifier, content)

    new_item = {
        'identifier': identifier,
        'content': content,
        'worth': worth,
        'created_cycle': session_data.get('cycle_count', 0)
    }

    storage.append(new_item)

    # Reorder storage after adding
    session_data['storage'] = sorted(storage, key=sort_by_identifier)

    # Find the new index after sorting
    new_index = next(i for i, item in enumerate(session_data['storage']) if item['identifier'] == identifier)

    return jsonify({
        'item': new_item,
        'index': new_index
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=port)
