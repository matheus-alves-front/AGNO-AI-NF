"""
Text-to-Speech Service usando ElevenLabs.

Este módulo fornece funcionalidade de conversão de texto para áudio
usando a API do ElevenLabs.
"""

import os
from pathlib import Path
from uuid import uuid4
from typing import Optional

from agno.utils.log import log_info, log_error


class TTSService:
    """Serviço para geração de áudio via ElevenLabs."""
    
    def __init__(
        self,
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
        model_id: str = "eleven_multilingual_v2",
        output_dir: str = "./storage/audio",
        api_key: Optional[str] = None,
    ):
        """
        Inicializa o serviço TTS.
        
        Args:
            voice_id: ID da voz ElevenLabs (default: George)
            model_id: Modelo TTS a usar (eleven_multilingual_v2 suporta PT-BR)
            output_dir: Diretório para salvar os áudios gerados
            api_key: API key ElevenLabs (default: ELEVEN_LABS_API_KEY env var)
        """
        try:
            from elevenlabs import ElevenLabs
        except ImportError:
            raise ImportError(
                "elevenlabs não instalado. Execute: pip install elevenlabs"
            )
        
        self.api_key = api_key or os.getenv("ELEVEN_LABS_API_KEY")
        if not self.api_key:
            log_error("ELEVEN_LABS_API_KEY não configurada!")
            raise ValueError("ELEVEN_LABS_API_KEY é obrigatória")
        
        self.client = ElevenLabs(api_key=self.api_key)
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_audio(
        self, 
        text: str, 
        filename: Optional[str] = None,
        output_format: str = "mp3_44100_64"
    ) -> str:
        """
        Gera áudio MP3 a partir de texto.
        
        Args:
            text: Texto para converter em áudio
            filename: Nome do arquivo (opcional, gera UUID se não fornecido)
            output_format: Formato de saída do áudio
            
        Returns:
            Caminho absoluto do arquivo de áudio gerado
        """
        if not filename:
            filename = f"{uuid4()}.mp3"
        
        if not filename.endswith(".mp3"):
            filename = f"{filename}.mp3"
        
        output_path = self.output_dir / filename
        
        try:
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format=output_format,
            )
            
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)
            
            log_info(f"Áudio gerado: {output_path}")
            return str(output_path.absolute())
            
        except Exception as e:
            log_error(f"Erro ao gerar áudio: {e}")
            raise
    
    def generate_summary_audio(
        self, 
        summary: str, 
        nfe_key: str
    ) -> str:
        """
        Gera áudio do resumo de uma auditoria de NFe.
        
        Args:
            summary: Resumo textual da auditoria
            nfe_key: Chave de acesso da NFe (usado como nome do arquivo)
            
        Returns:
            Caminho do arquivo de áudio
        """
        # Limita tamanho para economizar quota
        text = summary[:2000] if len(summary) > 2000 else summary
        
        filename = f"audit_{nfe_key[-8:]}.mp3"  # Usa últimos 8 dígitos
        return self.generate_audio(text, filename)


# Singleton para uso global
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Retorna instância singleton do TTSService."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
