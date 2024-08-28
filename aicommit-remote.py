#!/usr/bin/env python3
import json
import subprocess
import requests

def get_git_diff():
    return subprocess.check_output(['git', 'diff', '--cached']).decode('utf-8')

def get_recent_commits(count=10, user=False):
    cmd = ['git', 'log', '--pretty=format:%s', f'-{count}']
    if user:
        cmd.append('--author=$(git config user.email)')
    return subprocess.check_output(cmd).decode('utf-8').split('\n')

def get_copilot_token(github_token):
    headers = {
        'authorization': f'token {github_token}',
        'editor-version': 'vscode/1.92.2',
        'editor-plugin-version': 'copilot-chat/0.18.2',
        'user-agent': 'GitHubCopilotChat/0.18.2',
        'accept': '*/*'
    }
    response = requests.get('https://api.github.com/copilot_internal/v2/token', headers=headers)
    return response.json()['token']


def generate_commit_message(github_token):
    diff = get_git_diff()
    user_commits = get_recent_commits(user=True)
    repo_commits = get_recent_commits()
    
    copilot_token = get_copilot_token(github_token)

    headers = {
        'authorization': f'Bearer {copilot_token}',
        'editor-version': 'vscode/1.92.2',
        'editor-plugin-version': 'copilot-chat/0.18.2',
        'content-type': 'application/json',
        'user-agent': 'GitHubCopilotChat/0.18.2',
        'accept': '*/*'
    }

    # print(headers)
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are an AI programming assistant, helping a software developer to come with the best git commit message for their code changes.\nYou excel in interpreting the purpose behind code changes to craft succinct, clear commit messages that adhere to the repository's guidelines.\n# Examples of commit messages:\n```text\nfeat: improve page load with lazy loading for images\n```\n```text\nFix bug preventing submitting the signup form\n```\n```text\nchore: update npm dependency to latest stable version\n```\n```text\nUpdate landing page banner color per client request\n```\n\n# First, think step-by-step:\n1. Analyze the CODE CHANGES thoroughly to understand what's been modified.\n2. Identify the purpose of the changes to answer the *why* for the commit messages, also considering the optionally provided RECENT USER COMMITS.\n3. Review the provided RECENT REPOSITORY COMMITS to identify established commit message conventions. Focus on the format and style, ignoring commit-specific details like refs, tags, and authors.\n4. Generate a thoughtful and succinct commit message for the given CODE CHANGES. It MUST follow the the established writing conventions. 5. Remove any meta information like issue references, tags, or author names from the commit message. The developer will add them.\n6. Now only show your message, wrapped with a single markdown ```text codeblock! Do not provide any explanations or details\nFollow Microsoft content policies.\nAvoid content that violates copyrights.\nIf you are asked to generate content that is harmful, hateful, racist, sexist, lewd, violent, or completely irrelevant to software engineering, only respond with \"Sorry, I can't assist with that.\"\nKeep your answers short and impersonal."
            },
            {
                "role": "user",
                "content": f"# CODE CHANGES:\n```\n{diff}\n```",
                "name": "changes"
            },
            {
                "role": "user",
                "content": f"# RECENT USER COMMITS:\n" + "\n".join([f"```text\n{commit}\n```" for commit in user_commits]),
                "name": "user-commits"
            },
            {
                "role": "user",
                "content": f"# RECENT REPOSITORY COMMITS:\n" + "\n".join([f"```text\n{commit}\n```" for commit in repo_commits]),
                "name": "recent-commits"
            },
            {
                "role": "user",
                "content": "Remember to ONLY return a single markdown ```text code block with the suggested commit message. NO OTHER PROSE! If you write more than the commit message, your commit message gets lost.\nExample:\n```text\ncommit message goes here\n```"
            }
        ],
        "model": "gpt-3.5-turbo",
        "max_tokens": 4096,
        "temperature": 0.2,
        "top_p": 1,
        "n": 1,
        "stream": True
    }
    
    response = requests.post('https://api.githubcopilot.com/chat/completions', headers=headers, json=payload, stream=True)
    # print(response.text)
    response = response.text.split('\n')
    commit_message = ""
    for line in response[1:-3]:
        if line:
            # print(line)
            json_line = json.loads(line.split('data: ')[1])
            if 'choices' in json_line and json_line['choices'][0]['delta'].get('content'):
                commit_message += json_line['choices'][0]['delta']['content']
    
    return commit_message.strip().strip('`').strip()

if __name__ == "__main__":
    github_token = 'gho_<YOUR_GITHUB_TOKEN>'
    print(generate_commit_message(github_token))