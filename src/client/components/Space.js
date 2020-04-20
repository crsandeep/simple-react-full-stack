import { useEffect } from 'react';

/** @jsx React.DOM */
var _ = require('lodash');
var React = require('react/addons');
var fastclick = require('fastclick');
var Cell = require('./Cell.react');
var Timer = require('./Timer.react');
var CellActionCreators = require('../actions/CellActionCreators');
var SpaceRegionActionCreators = require('../actions/SpaceRegionActionCreators');
var MinesweeperStore = require('../stores/MinesweeperStore');

const SpaceRegion = () => {
//   getInitialState: function() {
//     return {
//       rows: this.props.rows,
//       isLost: this.props.isLost,
//       isWon: this.props.isWon
//     };
//   },


  const [rows, updateRows] = useState()

useEffect(() => {
    
    // fastclick.attach(document.body);
    // MinesweeperStore.addChangeListener(this._onChange, this);
  
    
}, []) 



//   showHelp: function(e) {
//     e.preventDefault();
//     alert("The purpose of the game is to open all the cells of the SpaceRegion which do not contain a bomb.\n\nYou lose if you set off a bomb cell.\n\nEvery non-bomb cell you open will tell you the total number of bombs in the eight neighboring cells.\n\nOnce you are sure that a cell contains a bomb, you can right-click to put a flag it on it as a reminder.\n\nTo start a new game (abandoning the current one), just click on the text that says 'Sweeper' at the top.\n\nUse the \"+\" and \"-\" buttons to change the size of the SpaceRegion.\n\n\nHappy mine hunting!");
//   },


  const getRows = () => {
    return rows.map((row) => {
      return (
        <tr>
          {getCells(row)}
        </tr>
      );
    })
  }

  const getCells = row => {
    var me = this;
    return _.map(row, function(cellInfo) {
      return me.getCellComponent(cellInfo);
    });
  }

  const getCellComponent = info => {
    return <Cell isBomb={info.isBomb}
                 isClicked={info.isClicked}
                 isFlagged={info.isFlagged}
                 bombCount={info.bombCount}
                 location={info.location}
                 onRightClick={this.cellRightClicked}
                 onOpen={this.cellClicked} />;
  }

  const onChange = () => {
    // var state = MinesweeperStore.getState()
    // this.setState({
    //   rows: state.rows,
    //   isLost: state.isLost,
    //   isWon: state.isWon
    // }, function() {
    //   var SpaceRegion = this.getDOMNode().parentNode;
    //   SpaceRegion.style.width = (this.state.rows.length * 31 + 1).toString() + "px";
    // });
  }

//   cellClicked: function(location) {
//     CellActionCreators.receiveClick(location);
//   }

//   cellRightClicked: function(location) {
//     CellActionCreators.receiveRightClick(location);
//   },
//   reset: function(e) {
//     e.preventDefault();
//     SpaceRegionActionCreators.receiveReset(this.state.rows.length);
//   },
//   resetBigger: function(e) {
//     e.preventDefault();
//     SpaceRegionActionCreators.receiveReset(this.state.rows.length + 1);
//   },
//   resetSmaller: function(e) {
//     e.preventDefault();
//     SpaceRegionActionCreators.receiveReset(this.state.rows.length - 1);
//   }
//   var storeState = MinesweeperStore.getState();
//   var isRunning = !storeState.isLost && !storeState.isWon && !storeState.isFreshSpaceRegion;
//   var cells = _.flatten(this.state.rows);
//   var totalBombs = _.filter(cells, function(c) { return c.isBomb }).length;
//   var totalFlags = _.filter(cells, function(c) { return c.isFlagged }).length;

// s
  return (
        <div>
          <div id='header'>
            <span className="bombs-remaining digital">{totalBombs - totalFlags}</span>
            <h3>
              <span onClick={resetSmaller} className='size-control'>-</span>
              <span onClick={reset} title='Reset' className={classes}>Sweeper</span>
              <span onClick={resetBigger} className='size-control'>+</span>
            </h3>
            <Timer isRunning={isRunning} />
          </div>
          <table>
            <tbody>
              {this.getRows()}
            </tbody>
          </table>
          <div id='footer'>
            <form onSubmit={this.showHelp}>
              <button id='help-btn'>Halp!</button>
            </form>
            <a target='_blank' href='http://github.com/willpiers/react-minesweeper'>
              <img id='github-logo' src='src/images/github.png'/>
            </a>
          </div>
        </div>
   
  )
}

export default SpaceRegion;
