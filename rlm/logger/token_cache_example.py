"""
Token Cache Tracking Example

This demonstrates how to track token cache usage from LLM responses
where cached_tokens is available in prompt_tokens_details.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm.logger import TimescaleDBClient, LLMInteractionRecord


# Initialize client
DB_URL = os.getenv("TIMESCALE_DB_URL", "postgresql://user:password@localhost:5432/rlm_logs")
client = TimescaleDBClient(DB_URL, pool_size=10)


# Example: LLM response with token cache details
def example_1_basic_cache_tracking():
    """Basic example: Tracking LLM response with cached_tokens."""
    print("\n" + "="*60)
    print("Example 1: Basic Token Cache Tracking")
    print("="*60)

    query_id = "benchmark-query-001"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Simulate LLM response with token cache details
    llm_response = {
        "choices": [{"message": {"content": "Hello world"}}],
        "usage": {
            "prompt_tokens": 1500,
            "completion_tokens": 20,
            "total_tokens": 1520,
            "prompt_tokens_details": {
                "cached_tokens": 1200  # This is what we want to track!
            }
        }
    }

    # Extract token cache info
    usage = llm_response["usage"]
    cached_tokens = usage["prompt_tokens_details"]["cached_tokens"]

    print(f"\nLLM Response Token Usage:")
    print(f"  Prompt tokens: {usage['prompt_tokens']}")
    print(f"  Cached tokens: {cached_tokens}")
    print(f"  Uncached tokens: {usage['prompt_tokens'] - cached_tokens}")
    print(f"  Completion tokens: {usage['completion_tokens']}")

    # Create LLM interaction record with cache tracking
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)

    record = LLMInteractionRecord(
        query_id=query_id,
        run_id=run_id,
        model="gpt-5",
        model_type="root",
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        total_tokens=usage["total_tokens"],
        cached_tokens=cached_tokens,  # Track cached tokens
        uncached_prompt_tokens=usage["prompt_tokens"] - cached_tokens,
        prompt_token_price=0.0015,  # $0.0015 per 1k tokens
        completion_token_price=0.006,  # $0.006 per 1k tokens
        duration_ms=150.5,
        start_time=start_time,
        end_time=end_time,
        success=True
    )

    interaction_id = client.record_llm_interaction(record)
    print(f"\nInteraction ID: {interaction_id}")

    client.complete_query_run(query_id, run_id)

    # Get cache summary
    print("\nToken Cache Summary:")
    cache_summary = client.get_token_cache_summary(query_id, run_id)
    if cache_summary:
        print(f"  Total prompt tokens: {cache_summary['total_prompt_tokens']}")
        print(f"  Total cached tokens: {cache_summary['total_cached_tokens']}")
        print(f"  Cache hit rate: {cache_summary['cache_hit_rate']:.2%}")
        print(f"  Total cost: ${cache_summary['total_cost']:.4f}")
        print(f"  Cache savings: {cache_summary['cache_savings_tokens']} tokens")


# Example: Multiple interactions showing cache evolution
def example_2_cache_evolution():
    """Track how cache usage evolves across multiple iterations."""
    print("\n" + "="*60)
    print("Example 2: Cache Evolution Across Iterations")
    print("="*60)

    query_id = "benchmark-query-002"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Simulate multiple LLM interactions with increasing cache usage
    for iteration in range(5):
        print(f"\nIteration {iteration + 1}:")
        
        client.set_context(iteration=iteration + 1)

        # Cache usage increases with each iteration
        base_prompt_tokens = 1000 + iteration * 200
        cached_tokens = 200 + iteration * 300  # More cache over time
        
        llm_response = {
            "usage": {
                "prompt_tokens": base_prompt_tokens,
                "completion_tokens": 50,
                "total_tokens": base_prompt_tokens + 50,
                "prompt_tokens_details": {
                    "cached_tokens": cached_tokens
                }
            }
        }

        usage = llm_response["usage"]
        
        print(f"  Prompt: {usage['prompt_tokens']} tokens")
        print(f"  Cached: {cached_tokens} tokens ({cached_tokens/usage['prompt_tokens']:.1%})")

        record = LLMInteractionRecord(
            query_id=query_id,
            run_id=run_id,
            model="gpt-5",
            model_type="root",
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
            cached_tokens=cached_tokens,
            prompt_token_price=0.0015,
            completion_token_price=0.006,
            duration_ms=100 + iteration * 10,
            success=True,
            metadata={"iteration": iteration + 1}
        )

        client.record_llm_interaction(record)

    client.complete_query_run(query_id, run_id)

    # Calculate and store cache optimization
    print("\nCalculating cache optimization...")
    client.calculate_and_store_cache_optimization(query_id, run_id)

    # Get optimization report
    print("\nToken Cache Optimization Report:")
    optimization = client.get_token_cache_optimization(query_id, run_id)
    if optimization:
        print(f"  Total prompt tokens: {optimization['total_prompt_tokens']}")
        print(f"  Total cached tokens: {optimization['total_cached_tokens']}")
        print(f"  Cache savings: {optimization['cache_savings_percentage']:.1%}")
        print(f"  Original cost: ${optimization['original_cost']:.4f}")
        print(f"  Cached cost: ${optimization['cached_cost']:.4f}")
        print(f"  Cost savings: ${optimization['cost_savings']:.4f} ({optimization['cost_savings_percentage']:.1%})")
        
        # Show cache evolution
        print("\nCache Evolution per Iteration:")
        cache_evolution = optimization.get('cache_evolution', [])
        if isinstance(cache_evolution, str):
            import json
            cache_evolution = json.loads(cache_evolution)
        
        for entry in cache_evolution:
            print(f"  Iteration {entry['iteration']}: "
                  f"{entry['prompt_tokens']} tokens, "
                  f"cache hit {entry['cache_hit_rate']:.1%}")


# Example: Cost comparison with and without cache
def example_3_cost_analysis():
    """Analyze cost savings from token cache."""
    print("\n" + "="*60)
    print("Example 3: Cost Analysis with Token Cache")
    print("="*60)

    query_id = "benchmark-query-003"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Model pricing (GPT-5 example)
    PRICING = {
        "prompt_per_1k": 0.0015,  # $0.0015 per 1k prompt tokens
        "completion_per_1k": 0.006  # $0.006 per 1k completion tokens
    }

    # Simulate a realistic conversation with cache
    interactions = [
        # Initial query - no cache
        {"prompt": 1000, "cached": 0, "completion": 100},
        # Follow-up - some cache
        {"prompt": 1500, "cached": 800, "completion": 150},
        # More follow-ups - increasing cache
        {"prompt": 2000, "cached": 1500, "completion": 200},
        {"prompt": 2500, "cached": 2000, "completion": 250},
    ]

    total_original_cost = 0
    total_cached_cost = 0

    print("\nInteraction Breakdown:")
    print("-" * 60)
    print(f"{'Iteration':<10} {'Prompt':<10} {'Cached':<10} {'Completion':<12} {'No Cache':<10} {'With Cache':<10} {'Savings':<10}")
    print("-" * 60)

    for i, interaction in enumerate(interactions, 1):
        prompt = interaction["prompt"]
        cached = interaction["cached"]
        completion = interaction["completion"]
        
        # Cost without cache
        cost_no_cache = (prompt * PRICING["prompt_per_1k"] + 
                        completion * PRICING["completion_per_1k"]) / 1000
        
        # Cost with cache (cached tokens are cheaper or free)
        # Assuming cached tokens are 50% cheaper in this example
        cached_prompt_price = PRICING["prompt_per_1k"] * 0.5
        cost_with_cache = ((prompt - cached) * PRICING["prompt_per_1k"] + 
                          cached * cached_prompt_price +
                          completion * PRICING["completion_per_1k"]) / 1000
        
        savings = cost_no_cache - cost_with_cache
        
        total_original_cost += cost_no_cache
        total_cached_cost += cost_with_cache
        
        print(f"{i:<10} {prompt:<10} {cached:<10} {completion:<12} "
              f"${cost_no_cache:<9.4f} ${cost_with_cache:<9.4f} ${savings:<9.4f}")

        # Record in database
        record = LLMInteractionRecord(
            query_id=query_id,
            run_id=run_id,
            model="gpt-5",
            model_type="root",
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
            cached_tokens=cached,
            uncached_prompt_tokens=prompt - cached,
            prompt_token_price=PRICING["prompt_per_1k"],
            completion_token_price=PRICING["completion_per_1k"],
            total_cost=cost_with_cache,
            duration_ms=200 + i * 50,
            success=True
        )
        
        client.record_llm_interaction(record)

    print("-" * 60)
    total_savings = total_original_cost - total_cached_cost
    savings_percentage = (total_savings / total_original_cost) * 100
    
    print(f"{'Total':<10} {'':<10} {'':<10} {'':<12} "
          f"${total_original_cost:<9.4f} ${total_cached_cost:<9.4f} ${total_savings:<9.4f}")
    print(f"\nOverall Savings: ${total_savings:.4f} ({savings_percentage:.1%})")

    client.complete_query_run(query_id, run_id)
    client.calculate_and_store_cache_optimization(query_id, run_id)


# Example: Real-world integration pattern
def example_4_real_world_integration():
    """Real-world pattern for integrating cache tracking."""
    print("\n" + "="*60)
    print("Example 4: Real-World Integration Pattern")
    print("="*60)

    query_id = "benchmark-query-004"
    run_id = datetime.now(timezone.utc)

    client.set_context(query_id=query_id, run_id=run_id)
    client.initialize_query_run(query_id, run_id)

    # Simulated LLM client with cache tracking
    class SimulatedLLMClient:
        def __init__(self, client, query_id, run_id):
            self.db_client = client
            self.query_id = query_id
            self.run_id = run_id
            self.iteration = 0
        
        def completion(self, messages, model="gpt-5"):
            """Simulate LLM completion with cache tracking."""
            self.iteration += 1
            
            # Simulate token usage with cache
            prompt_tokens = 1000 + len(messages) * 100
            cached_tokens = min(500 + self.iteration * 200, prompt_tokens - 100)
            completion_tokens = 50 + self.iteration * 20
            
            # Calculate cost
            prompt_price = 0.0015
            completion_price = 0.006
            
            # Cost with cache (assuming cached tokens are free)
            cost = ((prompt_tokens - cached_tokens) * prompt_price + 
                   completion_tokens * completion_price) / 1000
            
            # Create and store record
            record = LLMInteractionRecord(
                query_id=self.query_id,
                run_id=self.run_id,
                model=model,
                model_type="root",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cached_tokens=cached_tokens,
                uncached_prompt_tokens=prompt_tokens - cached_tokens,
                prompt_token_price=prompt_price,
                completion_token_price=completion_price,
                total_cost=cost,
                duration_ms=150 + self.iteration * 20,
                context_messages=len(messages),
                context_tokens=prompt_tokens,
                success=True,
                metadata={"iteration": self.iteration}
            )
            
            self.db_client.record_llm_interaction(record)
            
            # Return simulated response
            return {
                "choices": [{"message": {"content": "Simulated response"}}],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "prompt_tokens_details": {
                        "cached_tokens": cached_tokens
                    }
                }
            }

    # Usage
    llm = SimulatedLLMClient(client, query_id, run_id)
    
    print("\nSimulating conversation...")
    for i in range(3):
        messages = [{"role": "user", "content": f"Question {i+1}"}]
        response = llm.completion(messages)
        
        usage = response["usage"]
        print(f"  Iteration {i+1}: {usage['prompt_tokens']} prompt tokens, "
              f"{usage['prompt_tokens_details']['cached_tokens']} cached")

    client.complete_query_run(query_id, run_id)
    client.calculate_and_store_cache_optimization(query_id, run_id)

    # Get final report
    print("\nFinal Cache Report:")
    summary = client.get_token_cache_summary(query_id, run_id)
    if summary:
        print(f"  Total cost: ${summary['total_cost']:.4f}")
        print(f"  Cache hit rate: {summary['cache_hit_rate']:.2%}")
        print(f"  Interactions with cache: {summary['interactions_with_cache']}")


def main():
    """Run all examples."""
    print("\n" + "#"*60)
    print("# Token Cache Tracking Examples")
    print("#"*60)

    try:
        example_1_basic_cache_tracking()
        example_2_cache_evolution()
        example_3_cost_analysis()
        example_4_real_world_integration()

        print("\n" + "#"*60)
        print("# All examples completed successfully!")
        print("#"*60 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    main()
