<script lang="ts">
  type Method = 'mean' | 'median' | 'mode' | 'min' | 'max';
  
  interface Props {
    selectedMethod: Method;
    onSelect: (method: Method) => void;
  }
  
  let { selectedMethod, onSelect }: Props = $props();
  
  const methods: Method[] = ['mean', 'median', 'mode', 'min', 'max'];
</script>

<div class="mb-3">
  <label class="block text-xs font-medium text-gray-700 mb-2">
    Replacement Method
  </label>
  <div class="grid grid-cols-5 gap-2">
    {#each methods as method}
      <button
        type="button"
        role="button"
        tabindex="0"
        onclick={() => onSelect(method)}
        onkeydown={(e) => e.key === 'Enter' && onSelect(method)}
        class="px-3 py-2 text-xs rounded border-2 transition-all capitalize {selectedMethod === method ? 'border-primary-600 bg-primary-50 text-primary-900 font-semibold' : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'}"
      >
        {method}
      </button>
    {/each}
  </div>
</div>