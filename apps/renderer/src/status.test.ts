import { expect, test } from 'vitest';
import { label } from './status';

test('identifica el servicio', () => expect(label).toBe('Renderer aislado'));
