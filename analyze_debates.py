#!/usr/bin/env python3
"""
Script to analyze all debate summaries from output_consensus_* directories.
This script reads all summary_statistics.json files and provides aggregate statistics.
"""

import json
import os
import glob
from collections import defaultdict
from typing import Dict, List, Tuple


def find_output_directories() -> List[str]:
    """Find all output_consensus_* directories in the current working directory."""
    pattern = "output_consensus_*"
    directories = glob.glob(pattern)
    return sorted(directories)


def load_summary_file(directory: str) -> Dict:
    """Load and parse a summary_statistics.json file from a directory."""
    summary_path = os.path.join(directory, "summary_statistics.json")
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {summary_path}: {e}")
        return None


def analyze_debates() -> Tuple[Dict, List[Dict]]:
    """Analyze all debate summaries and return statistics and raw data."""
    directories = find_output_directories()
    
    if not directories:
        print("No output_consensus_* directories found!")
        return {}, []
    
    print(f"Found {len(directories)} output directories:")
    for dir_name in directories:
        print(f"  • {dir_name}")
    print()
    
    # Collect all summary data
    summaries = []
    for directory in directories:
        summary_data = load_summary_file(directory)
        if summary_data:
            summaries.append(summary_data)
    
    if not summaries:
        print("No valid summary files found!")
        return {}, []
    
    # Initialize statistics
    stats = {
        'total_debates': len(summaries),
        'wins_per_agent': defaultdict(int),
        'consensus_reached': 0,
        'rounds_data': [],
        'consensus_rounds_data': []
    }
    
    # Process each summary
    for summary in summaries:
        # Count wins per agent
        if 'debate_winner' in summary and summary['debate_winner']:
            winner = summary['debate_winner'].get('winner', 'Unknown')
            stats['wins_per_agent'][winner] += 1
        
        # Count consensus reached
        if summary.get('consensus_reached', False):
            stats['consensus_reached'] += 1
        
        # Collect rounds data
        if 'total_iterations' in summary:
            stats['rounds_data'].append(summary['total_iterations'])
        
        if 'consensus_rounds' in summary:
            stats['consensus_rounds_data'].append(summary['consensus_rounds'])
    
    return stats, summaries


def calculate_round_statistics(rounds_data: List[int]) -> Dict:
    """Calculate statistics for rounds data."""
    if not rounds_data:
        return {'avg': 0, 'min': 0, 'max': 0}
    
    return {
        'avg': sum(rounds_data) / len(rounds_data),
        'min': min(rounds_data),
        'max': max(rounds_data)
    }


def print_summary_report(stats: Dict, summaries: List[Dict]):
    """Print a formatted summary report."""
    print("=" * 60)
    print("🏆 DEBATE ANALYSIS SUMMARY REPORT")
    print("=" * 60)
    
    print(f"\n📊 OVERVIEW:")
    print(f"   Total Debates Analyzed: {stats['total_debates']}")
    print(f"   Consensus Reached: {stats['consensus_reached']} / {stats['total_debates']} ({stats['consensus_reached']/stats['total_debates']*100:.1f}%)")
    
    print(f"\n🏅 WINS PER AGENT:")
    if stats['wins_per_agent']:
        for agent, wins in sorted(stats['wins_per_agent'].items(), key=lambda x: x[1], reverse=True):
            percentage = (wins / stats['total_debates']) * 100
            print(f"   {agent}: {wins} wins ({percentage:.1f}%)")
    else:
        print("   No winner data available")
    
    # Presentation rounds statistics
    if stats['rounds_data']:
        rounds_stats = calculate_round_statistics(stats['rounds_data'])
        print(f"\n📈 PRESENTATION ROUNDS:")
        print(f"   Average: {rounds_stats['avg']:.1f}")
        print(f"   Minimum: {rounds_stats['min']}")
        print(f"   Maximum: {rounds_stats['max']}")
    
    # Consensus rounds statistics
    if stats['consensus_rounds_data']:
        consensus_stats = calculate_round_statistics(stats['consensus_rounds_data'])
        print(f"\n🔄 CONSENSUS ROUNDS:")
        print(f"   Average: {consensus_stats['avg']:.1f}")
        print(f"   Minimum: {consensus_stats['min']}")
        print(f"   Maximum: {consensus_stats['max']}")
    
    print(f"\n📁 DETAILED BREAKDOWN:")
    for i, summary in enumerate(summaries, 1):
        topic = summary.get('topic', 'Unknown Topic')
        consensus = "✅" if summary.get('consensus_reached', False) else "❌"
        iterations = summary.get('total_iterations', 'N/A')
        consensus_rounds = summary.get('consensus_rounds', 'N/A')
        winner = summary.get('debate_winner', {}).get('winner', 'N/A')
        
        print(f"   {i:2d}. {consensus} {topic[:50]}{'...' if len(topic) > 50 else ''}")
        print(f"       Iterations: {iterations}, Consensus Rounds: {consensus_rounds}, Winner: {winner}")


def main():
    """Main function to run the debate analysis."""
    print("🔍 Analyzing debate summaries...")
    print()
    
    try:
        stats, summaries = analyze_debates()
        
        if stats and summaries:
            print_summary_report(stats, summaries)
        else:
            print("❌ No data to analyze.")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 