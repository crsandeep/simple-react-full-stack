const generateSpaceRegion = (width, height, suns, drones) => {
    let defaultSpaceRegionState = []
    for (let i = 0 ; i < height; i ++) {

      let row = []
      for (let j = 0; j < width; j ++) {
        row.push(squareState(j, i, suns, drones))
      }
      defaultSpaceRegionState.push(row)
    }
    return defaultSpaceRegionState
   
  }

  const squareState = (xIndex, yIndex, suns, drones) => {
    const hasSun = Boolean(suns.find(({ x, y }) => x === xIndex && y === yIndex))
    const hasDrone = Boolean(drones.find(({ x, y }) => x === xIndex && y === yIndex))

    return {
      explored: hasDrone,
      hasSun: hasSun,
      hasStar: Boolean(Math.random() < 0.5),
      hasDrone: hasDrone,
      hasBarrier: false
    }
     
  }

  export default generateSpaceRegion