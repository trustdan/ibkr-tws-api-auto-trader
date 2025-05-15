import { describe, it, expect } from 'vitest';
import pkg from '../../package.json';

describe('App Version', () => {
  it('should have a valid version in package.json', () => {
    expect(pkg.version).toBeDefined();
    expect(pkg.version).toMatch(/^\d+\.\d+\.\d+(-\w+)?$/);
  });
}); 