import { test, expect, type Page } from '@playwright/test';

// Suíte E2E — Interface de chat.
// Roda contra o servidor local real (uvicorn), não contra mocks do backend na parte funcional.
// Pré-requisito: `uvicorn app:app --port 8000` rodando antes de `npx playwright test`.

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:8000';

test.describe('Funcional essencial', () => {
  test('digitar uma pergunta real e ver a resposta aparecer', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByRole('textbox').fill('Depois que um reembolso é aprovado, quanto tempo demora para eu receber o dinheiro de volta?');
    await page.getByRole('button', { name: /enviar/i }).click();

    const resposta = page.locator('.mensagem.assistente').last();
    await expect(resposta).not.toHaveText('Digitando...', { timeout: 15_000 });
    await expect(resposta).toContainText(/dias úteis/i);
  });

  test('histórico da conversa permanece visível após uma segunda pergunta', async ({ page }) => {
    await page.goto(BASE_URL);

    await page.getByRole('textbox').fill('Quais formas de pagamento a BimBam Buy aceita?');
    await page.getByRole('button', { name: /enviar/i }).click();
    await expect(page.locator('.mensagem.assistente').last()).not.toHaveText('Digitando...', { timeout: 15_000 });

    await page.getByRole('textbox').fill('Quanto tempo demora para meu pedido chegar?');
    await page.getByRole('button', { name: /enviar/i }).click();
    await expect(page.locator('.mensagem.assistente').last()).not.toHaveText('Digitando...', { timeout: 15_000 });

    // as duas trocas (2 perguntas + 2 respostas = 4 mensagens) devem estar todas visíveis
    await expect(page.locator('.mensagem.usuario')).toHaveCount(2);
    await expect(page.locator('.mensagem.assistente')).toHaveCount(2);
  });

  test('pergunta fora de escopo retorna mensagem de não encontrado', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByRole('textbox').fill('Qual é a capital da Mongólia?');
    await page.getByRole('button', { name: /enviar/i }).click();

    const resposta = page.locator('.mensagem.assistente').last();
    await expect(resposta).not.toHaveText('Digitando...', { timeout: 15_000 });
    await expect(resposta).toContainText(/não encontrei/i);
  });

  test('tecla Enter submete o formulário', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.getByRole('textbox').fill('Como funciona o programa de afiliados?');
    await page.getByRole('textbox').press('Enter');

    // se Enter não submeter, isto nunca deixa de mostrar "Digitando..." nem aparece mensagem nova
    await expect(page.locator('.mensagem.assistente').last()).not.toHaveText('Digitando...', { timeout: 15_000 });
    await expect(page.locator('.mensagem.usuario')).toHaveCount(1);
  });

  test('viewport mobile permanece usável sem overflow horizontal', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(BASE_URL);

    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1); // +1 tolerância de arredondamento

    await expect(page.getByRole('textbox')).toBeVisible();
    await expect(page.getByRole('button', { name: /enviar/i })).toBeVisible();
  });
});

test.describe('Resiliência a falhas de backend', () => {
  async function interceptarPerguntar(page: Page, fulfill: Parameters<Page['route']>[1]) {
    await page.route('**/perguntar', fulfill);
  }

  test('erro 500 do backend exibe mensagem amigável, sem travar a UI', async ({ page }) => {
    await interceptarPerguntar(page, (route) =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'erro interno' }) })
    );

    const erros: string[] = [];
    page.on('pageerror', (err) => erros.push(err.message));

    await page.goto(BASE_URL);
    await page.getByRole('textbox').fill('Qualquer pergunta');
    await page.getByRole('button', { name: /enviar/i }).click();

    // Em caso de erro, o frontend remove a bolha "Digitando..." (classe .assistente)
    // e cria uma nova bolha com classe .erro — não reaproveita .assistente. A asserção
    // original checava .mensagem.assistente, que nunca deixa de existir como
    // "Digitando..." (ela é removida, não atualizada), causando falso negativo.
    const resposta = page.locator('.mensagem.erro').last();
    await expect(resposta).toBeVisible({ timeout: 10_000 });
    await expect(resposta).not.toHaveText(''); // não pode ficar em branco/undefined
    await expect(page.locator('.mensagem.assistente', { hasText: 'Digitando...' })).toHaveCount(0);
    expect(erros).toEqual([]); // nenhuma exceção JS não tratada
  });

  test('latência alta mantém indicador de carregamento sem travar', async ({ page }) => {
    await interceptarPerguntar(page, async (route) => {
      await new Promise((r) => setTimeout(r, 4000));
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ resposta: 'Resposta atrasada, mas entregue.' }) });
    });

    await page.goto(BASE_URL);
    await page.getByRole('textbox').fill('Pergunta com latência simulada');
    await page.getByRole('button', { name: /enviar/i }).click();

    // logo após enviar, ainda deve estar em "Digitando..."
    await expect(page.locator('.mensagem.assistente').last()).toHaveText('Digitando...');
    // e eventualmente resolve para a resposta real, sem travar
    await expect(page.locator('.mensagem.assistente').last()).toContainText('Resposta atrasada', { timeout: 8_000 });
  });

  test('corpo de resposta vazio/malformado não quebra a UI com exceção não tratada', async ({ page }) => {
    await interceptarPerguntar(page, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    );

    const erros: string[] = [];
    page.on('pageerror', (err) => erros.push(err.message));

    await page.goto(BASE_URL);
    await page.getByRole('textbox').fill('Pergunta com resposta malformada');
    await page.getByRole('button', { name: /enviar/i }).click();

    await page.waitForTimeout(2000); // tempo para eventual erro JS se manifestar
    expect(erros).toEqual([]);
  });
});
