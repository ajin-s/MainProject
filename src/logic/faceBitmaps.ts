import { EmotionState } from '../types';

export const FACE_BITMAPS: Record<EmotionState, string> = {
  idle: 
`    ( - )        ( - )    
                          
         -------          `,

  watching: 
`    ( O )        ( O )    
                          
         =======          `,

  listening: 
`    ( ^ )        ( ^ )    
      |            |      
         -------          `,

  thinking: 
`    ( > )        ( < )    
            ?             
         - - - -          `,

  curious: 
`   / ( o ) \\    / ( O ) \\
            ?             
         (  o  )          `,

  happy: 
`    ( ^ )        ( ^ )    
          \\____/          
         \\______/         `,

  concerned: 
`    ( - )        ( - )    
     /            \\       
         /------\\         `,

  alert: 
`   ! ( O ) !    ! ( O ) !
          !!!!!!          
         [======]         `,
};

export function getFaceArt(emotion: string): string {
  const key = (emotion?.toLowerCase() || 'idle') as EmotionState;
  return FACE_BITMAPS[key] || FACE_BITMAPS.idle;
}
