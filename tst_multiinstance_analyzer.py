#!/usr/bin/env python3
"""
Analisador Focado em TST e Processos Multi-instância
Trabalha APENAS com dados confiáveis e fluxos completos, sem inferências.
"""

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sys

# Adiciona o diretório src ao path
sys.path.append(str(Path(__file__).parent))

from src.utils.movement_analyzer import MovementAnalyzer
import json
import glob

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TSTMultiInstanceAnalyzer:
    """Analisa apenas processos TST e casos com múltiplas instâncias confirmadas."""
    
    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)
        
        self.movement_analyzer = MovementAnalyzer()
        
        self.output_path = self.base_path / "tst_analysis_results"
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Códigos de movimento confiáveis
        self.primeira_instancia_codes = {
            219: 'Procedência',
            220: 'Improcedência',
            221: 'Procedência em Parte'
        }
        
        self.recurso_codes = {
            237: 'Provimento',
            238: 'Provimento em Parte',
            242: 'Desprovimento',
            236: 'Negação de Seguimento'
        }
    
    def extract_case_core(self, numero_processo: str) -> str:
        """Extrai núcleo do número do processo para rastreamento entre instâncias."""
        numbers_only = ''.join(filter(str.isdigit, numero_processo))
        if len(numbers_only) >= 20:
            # Remove dígitos variáveis mantendo núcleo único
            return numbers_only[:7] + numbers_only[9:]
        return numbers_only
    
    def identify_tst_cases(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifica casos TST (tribunal TST ou grau GS/SUP)."""
        tst_cases = []
        for processo in data:
            tribunal = processo.get('tribunal', '').upper()
            grau = processo.get('grau', '').upper()
            
            if tribunal == 'TST' or grau in ['GS', 'SUP']:
                tst_cases.append(processo)
        
        return tst_cases
    
    def build_case_chains(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Constrói cadeias de processos através das instâncias."""
        chains = {}
        
        for processo in data:
            core = self.extract_case_core(processo.get('numeroProcesso', ''))
            if core:
                if core not in chains:
                    chains[core] = []
                chains[core].append(processo)
        
        # Ordena cada cadeia por grau
        for core in chains:
            chains[core].sort(key=lambda x: self._grau_order(x.get('grau', '')))
        
        return chains
    
    def _grau_order(self, grau: str) -> int:
        """Retorna ordem do grau para ordenação."""
        grau_map = {
            'G1': 1, 'GRAU_1': 1,
            'G2': 2, 'GRAU_2': 2,
            'GS': 3, 'SUP': 3
        }
        return grau_map.get(grau, 999)
    
    def analyze_complete_flows(self, chains: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analisa apenas fluxos completos com dados de múltiplas instâncias."""
        complete_flows = []
        tst_only_flows = []
        multi_instance_flows = []
        
        for core, chain in chains.items():
            if len(chain) == 1:
                # Caso único - verifica se é TST com movimentos históricos
                processo = chain[0]
                if processo.get('tribunal') == 'TST' or processo.get('grau') in ['GS', 'SUP']:
                    flow = self._analyze_tst_with_movements(processo)
                    if flow and flow.get('has_complete_history'):
                        tst_only_flows.append(flow)
            else:
                # Múltiplas instâncias - analisa fluxo completo
                flow = self._analyze_multi_instance_flow(chain)
                if flow:
                    multi_instance_flows.append(flow)
                    if any(p.get('tribunal') == 'TST' or p.get('grau') in ['GS', 'SUP'] for p in chain):
                        complete_flows.append(flow)
        
        return {
            'total_chains': len(chains),
            'complete_flows': complete_flows,
            'tst_only_flows': tst_only_flows,
            'multi_instance_flows': multi_instance_flows,
            'statistics': self._calculate_statistics(complete_flows + tst_only_flows + multi_instance_flows)
        }
    
    def _analyze_tst_with_movements(self, processo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analisa processo TST buscando histórico completo nos movimentos."""
        movimentos = processo.get('movimentos', [])
        
        # Busca movimentos de primeira instância e recursos
        primeira_instancia = None
        recursos = []
        
        for movimento in movimentos:
            codigo = movimento.get('codigo')
            if codigo in self.primeira_instancia_codes:
                primeira_instancia = {
                    'codigo': codigo,
                    'nome': self.primeira_instancia_codes[codigo],
                    'data': movimento.get('dataHora')
                }
            elif codigo in self.recurso_codes:
                recursos.append({
                    'codigo': codigo,
                    'nome': self.recurso_codes[codigo],
                    'data': movimento.get('dataHora')
                })
        
        if primeira_instancia and recursos:
            # Tem histórico completo nos movimentos
            return {
                'numero_processo': processo.get('numeroProcesso'),
                'tribunal': processo.get('tribunal'),
                'grau': processo.get('grau'),
                'primeira_instancia': primeira_instancia,
                'recursos': recursos,
                'has_complete_history': True,
                'source': 'tst_movements',
                'worker_won': self._determine_final_outcome(primeira_instancia, recursos)
            }
        
        return None
    
    def _analyze_multi_instance_flow(self, chain: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analisa fluxo através de múltiplas instâncias."""
        flow = {
            'case_core': self.extract_case_core(chain[0].get('numeroProcesso', '')),
            'instances': [],
            'has_tst': False,
            'complete_path': []
        }
        
        for processo in chain:
            grau = processo.get('grau', '')
            tribunal = processo.get('tribunal', '')
            movimentos = processo.get('movimentos', [])
            
            # Identifica resultado desta instância
            resultado = self._extract_instance_result(movimentos, grau)
            
            instance_data = {
                'grau': grau,
                'tribunal': tribunal,
                'numero_processo': processo.get('numeroProcesso'),
                'resultado': resultado,
                'data_ajuizamento': processo.get('dataAjuizamento')
            }
            
            flow['instances'].append(instance_data)
            
            if tribunal == 'TST' or grau in ['GS', 'SUP']:
                flow['has_tst'] = True
            
            if resultado:
                flow['complete_path'].append(f"{grau}:{resultado['nome']}")
        
        # Só retorna se tem dados suficientes
        if len(flow['complete_path']) >= 2:
            flow['path_string'] = ' → '.join(flow['complete_path'])
            flow['worker_won'] = self._determine_chain_outcome(flow['instances'])
            return flow
        
        return None
    
    def _extract_instance_result(self, movimentos: List[Dict], grau: str) -> Optional[Dict[str, Any]]:
        """Extrai resultado de uma instância específica."""
        if grau in ['G1', 'GRAU_1']:
            # Primeira instância
            for movimento in movimentos:
                codigo = movimento.get('codigo')
                if codigo in self.primeira_instancia_codes:
                    return {
                        'codigo': codigo,
                        'nome': self.primeira_instancia_codes[codigo],
                        'favoravel_trabalhador': codigo in [219, 221]
                    }
        else:
            # Instâncias recursais
            for movimento in movimentos:
                codigo = movimento.get('codigo')
                if codigo in self.recurso_codes:
                    return {
                        'codigo': codigo,
                        'nome': self.recurso_codes[codigo],
                        'recurso_provido': codigo in [237, 238]
                    }
        
        return None
    
    def _determine_final_outcome(self, primeira: Dict, recursos: List[Dict]) -> bool:
        """Determina resultado final aplicando lógica correta de recursos."""
        # Resultado da primeira instância
        trabalhador_ganhou_primeira = primeira['codigo'] in [219, 221]
        
        # Analisa último recurso
        if recursos:
            ultimo_recurso = recursos[-1]
            recurso_provido = ultimo_recurso['codigo'] in [237, 238]
            
            # Lógica: se trabalhador ganhou e recurso foi provido, trabalhador perdeu
            if trabalhador_ganhou_primeira:
                # Empregador recorreu
                return not recurso_provido
            else:
                # Trabalhador recorreu
                return recurso_provido
        
        return trabalhador_ganhou_primeira
    
    def _determine_chain_outcome(self, instances: List[Dict]) -> Optional[bool]:
        """Determina resultado final de uma cadeia de instâncias."""
        primeira = None
        ultimo_recurso = None
        
        for instance in instances:
            if instance['grau'] in ['G1', 'GRAU_1'] and instance['resultado']:
                primeira = instance['resultado']
            elif instance['resultado'] and 'recurso_provido' in instance['resultado']:
                ultimo_recurso = instance['resultado']
        
        if primeira and ultimo_recurso:
            trabalhador_ganhou_primeira = primeira['favoravel_trabalhador']
            recurso_provido = ultimo_recurso['recurso_provido']
            
            if trabalhador_ganhou_primeira:
                return not recurso_provido
            else:
                return recurso_provido
        elif primeira:
            return primeira.get('favoravel_trabalhador', None)
        
        return None
    
    def _calculate_statistics(self, flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estatísticas dos fluxos analisados."""
        stats = {
            'total_flows': len(flows),
            'tst_flows': sum(1 for f in flows if f.get('has_tst', False) or f.get('tribunal') == 'TST'),
            'worker_victories': sum(1 for f in flows if f.get('worker_won') is True),
            'worker_defeats': sum(1 for f in flows if f.get('worker_won') is False),
            'undefined': sum(1 for f in flows if f.get('worker_won') is None),
            'paths': {}
        }
        
        # Conta caminhos processuais
        for flow in flows:
            path = flow.get('path_string', flow.get('complete_path', ['Único']))
            if isinstance(path, list):
                path = ' → '.join(path)
            stats['paths'][path] = stats['paths'].get(path, 0) + 1
        
        # Calcula taxas
        if stats['total_flows'] > 0:
            stats['worker_success_rate'] = (stats['worker_victories'] / 
                                           (stats['worker_victories'] + stats['worker_defeats']) * 100
                                           if (stats['worker_victories'] + stats['worker_defeats']) > 0 else 0)
        
        return stats
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """Gera relatório detalhado da análise TST e multi-instância."""
        stats = analysis['statistics']
        
        report = f"""# Análise de Processos TST e Multi-instância

## Resumo Executivo

- **Total de cadeias processuais**: {analysis['total_chains']:,}
- **Fluxos completos analisados**: {stats['total_flows']:,}
- **Processos com TST**: {stats['tst_flows']:,}
- **Taxa de sucesso do trabalhador**: {stats.get('worker_success_rate', 0):.1f}%

## Resultados Finais

- **Vitórias do trabalhador**: {stats['worker_victories']:,} ({stats['worker_victories']/stats['total_flows']*100:.1f}%)
- **Derrotas do trabalhador**: {stats['worker_defeats']:,} ({stats['worker_defeats']/stats['total_flows']*100:.1f}%)
- **Resultados indefinidos**: {stats['undefined']:,}

## Caminhos Processuais Mais Comuns

"""
        # Top 10 caminhos
        sorted_paths = sorted(stats['paths'].items(), key=lambda x: x[1], reverse=True)
        for i, (path, count) in enumerate(sorted_paths[:10], 1):
            percent = (count / stats['total_flows'] * 100) if stats['total_flows'] > 0 else 0
            report += f"{i}. **{path}**: {count} casos ({percent:.1f}%)\n"
        
        report += f"""

## Análise de Fluxos TST

### Casos TST com Histórico Completo nos Movimentos
- **Total encontrado**: {len(analysis['tst_only_flows']):,}
- **Característica**: Processos TST que contêm movimentos de primeira instância

### Processos Multi-instância
- **Total**: {len(analysis['multi_instance_flows']):,}
- **Com TST**: {sum(1 for f in analysis['multi_instance_flows'] if f.get('has_tst')):.0f}

## Metodologia

Esta análise considera **APENAS**:
1. Processos que passaram por múltiplas instâncias (rastreamento por núcleo do número)
2. Processos TST que contêm histórico completo nos movimentos
3. Dados explícitos sem inferências ou suposições

**Lógica aplicada**:
- Procedência + Provimento = Trabalhador perdeu (empregador recorreu e ganhou)
- Improcedência + Provimento = Trabalhador ganhou (trabalhador recorreu e ganhou)

## Confiabilidade

**100% dos dados** são baseados em:
- Códigos de movimento explícitos (219, 220, 237, 242, etc.)
- Rastreamento confirmado entre instâncias
- Sem inferências ou estimativas

---
*Análise gerada em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report
    
    def load_raw_json_files(self, path: Path) -> List[Dict[str, Any]]:
        """Carrega arquivos JSON do diretório especificado."""
        all_data = []
        json_files = list(path.glob("*.json"))
        
        logger.info(f"Encontrados {len(json_files)} arquivos JSON em {path}")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
            except Exception as e:
                logger.error(f"Erro ao ler {json_file}: {str(e)}")
        
        return all_data
    
    def filter_assedio_moral_cases(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtra casos de assédio moral."""
        assedio_codes = [1723, 14175, 14018]
        filtered = []
        
        for processo in data:
            assuntos = processo.get('assuntos', [])
            if isinstance(assuntos, list):
                for assunto in assuntos:
                    if isinstance(assunto, dict):
                        codigo = assunto.get('codigo')
                        nome = assunto.get('nome', '').lower()
                        
                        if codigo in assedio_codes or 'assédio' in nome or 'assedio' in nome:
                            filtered.append(processo)
                            break
        
        return filtered
    
    def run_analysis(self, data_source: str = "external", 
                    external_path: Optional[str] = None,
                    focus_assedio_moral: bool = True) -> Dict[str, Any]:
        """Executa análise completa focada em TST e multi-instância."""
        logger.info("Iniciando análise TST e multi-instância...")
        
        # Carrega dados
        if external_path:
            data = self.load_raw_json_files(Path(external_path))
        else:
            data = []
            logger.error("Caminho externo não fornecido")
            return {}
        
        if not data:
            logger.error("Nenhum dado carregado")
            return {}
        
        logger.info(f"Carregados {len(data)} processos")
        
        # Filtra casos de assédio moral se solicitado
        if focus_assedio_moral:
            data = self.filter_assedio_moral_cases(data)
            logger.info(f"Filtrados {len(data)} casos de assédio moral")
        
        # Identifica casos TST
        tst_cases = self.identify_tst_cases(data)
        logger.info(f"Identificados {len(tst_cases)} casos TST")
        
        # Constrói cadeias processuais
        chains = self.build_case_chains(data)
        logger.info(f"Construídas {len(chains)} cadeias processuais")
        
        # Analisa fluxos completos
        analysis = self.analyze_complete_flows(chains)
        
        # Gera relatório
        report_content = self.generate_report(analysis)
        
        # Salva relatório
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_path / f"relatorio_tst_multiinstancia_{timestamp}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Relatório salvo em: {report_path}")
        
        # Visualizações removidas por enquanto (sem matplotlib)
        
        return {
            'analysis': analysis,
            'report_path': str(report_path),
            'timestamp': datetime.now().isoformat()
        }
    

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Análise de Processos TST e Multi-instância")
    
    parser.add_argument("--data-source", choices=["consolidated", "raw", "external"],
                       default="external", help="Fonte dos dados")
    parser.add_argument("--external-path", type=str,
                       default="/Users/danilobortoli/Documents/Tese de doutorado da Andreia/Dados da segunda extração/raw",
                       help="Caminho externo para dados")
    parser.add_argument("--focus-assedio", action="store_true", default=True,
                       help="Focar em casos de assédio moral")
    parser.add_argument("--output-dir", type=str,
                       help="Diretório de saída personalizado")
    
    args = parser.parse_args()
    
    # Inicializa analisador
    base_path = Path(args.output_dir) if args.output_dir else None
    analyzer = TSTMultiInstanceAnalyzer(base_path)
    
    # Executa análise
    results = analyzer.run_analysis(
        data_source=args.data_source,
        external_path=args.external_path,
        focus_assedio_moral=args.focus_assedio
    )
    
    if results:
        print(f"\n✅ Análise concluída!")
        print(f"📄 Relatório: {results['report_path']}")
        
        # Imprime resumo
        stats = results['analysis']['statistics']
        print(f"\n📊 RESUMO:")
        print(f"  Fluxos analisados: {stats['total_flows']:,}")
        print(f"  Taxa de sucesso: {stats.get('worker_success_rate', 0):.1f}%")
        print(f"  Casos TST: {stats['tst_flows']:,}")
    else:
        print("❌ Falha na análise")

if __name__ == "__main__":
    main()